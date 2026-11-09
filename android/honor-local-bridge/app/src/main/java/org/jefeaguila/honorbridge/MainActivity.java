package org.jefeaguila.honorbridge;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.documentfile.provider.DocumentFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final int REQUEST_TREE = 101;
    private static final int MAX_FILES = 20000, MAX_DEPTH = 32, MAX_NODES = 40000;
    private static final int MAX_EDIT_BYTES = 2 * 1024 * 1024;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView status, scope;
    private DocumentFile root;
    private Uri treeUri;
    private volatile JSONObject lastReport;
    private final List<DocumentFile> visibleFiles = new ArrayList<>();

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(18);
        page.setPadding(pad,pad,pad,pad);
        TextView title = new TextView(this);
        title.setText("AEGIS · HONOR LOCAL BRIDGE");
        title.setTextSize(22);
        page.addView(title);
        TextView note = new TextView(this);
        note.setText("Local Android files only. No Termux, root, cloud provider, network permission, or background server.");
        page.addView(note);
        scope = new TextView(this);
        scope.setText("Scope: no folder selected");
        page.addView(scope);
        addButton(page,"Choose local folder",v -> chooseFolder());
        addButton(page,"Scan + SHA-256 inventory",v -> scanTree());
        addButton(page,"Browse / edit / share file",v -> browseFiles());
        addButton(page,"Create text file",v -> createTextFile());
        addButton(page,"Export last scan report",v -> exportReport());
        status = new TextView(this);
        status.setText("Ready. Choose a local folder.");
        page.addView(status);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(page);
        setContentView(scroll);
        restoreScope();
    }

    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }

    private void addButton(LinearLayout page,String label,android.view.View.OnClickListener click) {
        Button b = new Button(this);
        b.setText(label);
        b.setOnClickListener(click);
        page.addView(b,new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
    }

    private void chooseFolder() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(i,REQUEST_TREE);
    }

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode != REQUEST_TREE || resultCode != RESULT_OK || data == null) return;
        Uri selected = data.getData();
        if(selected == null || !LocalScopePolicy.isLocalAuthority(selected.getAuthority())) {
            setStatus("Rejected. Select a folder from this phone's local shared storage.");
            return;
        }
        try {
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            getContentResolver().takePersistableUriPermission(selected,flags);
            treeUri = selected;
            root = DocumentFile.fromTreeUri(this,selected);
            getSharedPreferences("local_scope",MODE_PRIVATE).edit().putString("tree_uri",selected.toString()).apply();
            updateScope();
            setStatus("Saved folder grant for this Android app profile.");
        } catch(Exception e) { setStatus("Folder permission error: " + e.getMessage()); }
    }

    private void restoreScope() {
        String saved = getSharedPreferences("local_scope",MODE_PRIVATE).getString("tree_uri",null);
        if(saved == null) return;
        try {
            Uri candidate = Uri.parse(saved);
            if(LocalScopePolicy.isLocalAuthority(candidate.getAuthority())) {
                treeUri = candidate;
                root = DocumentFile.fromTreeUri(this,candidate);
                updateScope();
            }
        } catch(Exception e) { setStatus("Folder grant expired. Choose the folder again."); }
    }

    private boolean ensureScope() {
        if(root != null && root.canRead() && root.canWrite()) return true;
        setStatus("Choose a local folder and grant read/write access first.");
        return false;
    }

    private void updateScope() {
        scope.setText("Scope: " + (root == null ? "none" : root.getName())
                + "\nProvider: Android local shared storage\nNetwork: disabled");
    }

    private void setStatus(String s) { if(status != null) status.setText(s); }

    private void scanTree() {
        if(!ensureScope()) return;
        setStatus("Scanning selected folder and hashing files…");
        worker.execute(() -> {
            try {
                JSONObject report = new JSONObject();
                JSONArray records = new JSONArray();
                int[] counts = new int[]{0,0,0};
                walk(root,"",0,records,counts);
                report.put("schema","aegis-honor-local-scan/v1");
                report.put("created_at",new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX",Locale.US).format(new Date()));
                report.put("scope_name",root.getName());
                report.put("file_count",counts[0]);
                report.put("directory_count",counts[1]);
                report.put("entries_visited",counts[2]);
                report.put("truncated",counts[0] >= MAX_FILES || counts[2] >= MAX_NODES);
                report.put("files",records);
                lastReport = report;
                try(OutputStream out = openFileOutput("last_local_scan.json",MODE_PRIVATE)) {
                    out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));
                }
                runOnUiThread(() -> setStatus("Scan complete. Files: " + counts[0]
                        + " · Folders: " + counts[1] + " · Entries: " + counts[2]
                        + "\nReport saved in app-private storage. Export copies it to the chosen folder."));
            } catch(Exception e) { runOnUiThread(() -> setStatus("Scan error: " + e.getMessage())); }
        });
    }

    private void walk(DocumentFile node,String path,int depth,JSONArray records,int[] counts) throws Exception {
        if(depth > MAX_DEPTH || counts[0] >= MAX_FILES || counts[2] >= MAX_NODES) return;
        counts[2]++;
        if(node.isDirectory()) {
            counts[1]++;
            DocumentFile[] children = node.listFiles();
            Arrays.sort(children,Comparator.comparing(f -> f.getName() == null ? "" : f.getName().toLowerCase(Locale.ROOT)));
            for(DocumentFile child : children) {
                String name = child.getName() == null ? "(unnamed)" : child.getName();
                walk(child,path.isEmpty() ? name : path + "/" + name,depth+1,records,counts);
                if(counts[0] >= MAX_FILES || counts[2] >= MAX_NODES) break;
            }
        } else if(node.isFile()) {
            counts[0]++;
            JSONObject item = new JSONObject();
            item.put("path",path);
            item.put("mime_type",node.getType());
            item.put("size_bytes",node.length());
            item.put("modified_at_epoch_ms",node.lastModified());
            try { item.put("sha256",sha256(node.getUri())); }
            catch(Exception e) { item.put("hash_error",e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage())); }
            records.put(item);
        }
    }

    private String sha256(Uri uri) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try(InputStream in = getContentResolver().openInputStream(uri)) {
            if(in == null) throw new IllegalStateException("No input stream");
            byte[] buf = new byte[65536]; int n;
            while((n = in.read(buf)) != -1) digest.update(buf,0,n);
        }
        StringBuilder hex = new StringBuilder();
        for(byte b : digest.digest()) hex.append(String.format(Locale.ROOT,"%02x",b));
        return hex.toString();
    }

    private void browseFiles() {
        if(!ensureScope()) return;
        DocumentFile[] files = root.listFiles();
        Arrays.sort(files,Comparator.comparing(f -> f.getName() == null ? "" : f.getName().toLowerCase(Locale.ROOT)));
        visibleFiles.clear();
        List<String> labels = new ArrayList<>();
        for(DocumentFile f : files) {
            visibleFiles.add(f);
            labels.add((f.isDirectory() ? "[DIR] " : "[FILE] ") + (f.getName() == null ? "(unnamed)" : f.getName()));
        }
        if(labels.isEmpty()) { setStatus("Selected folder is empty."); return; }
        new AlertDialog.Builder(this).setTitle("Selected folder")
                .setItems(labels.toArray(new String[0]),(d,w) -> showFileActions(visibleFiles.get(w))).show();
    }

    private void showFileActions(DocumentFile file) {
        if(file.isDirectory()) { setStatus("Folder: " + file.getName() + ". Use Scan for nested inventory."); return; }
        String[] actions = {"Details","Edit text file","Share selected file…"};
        new AlertDialog.Builder(this).setTitle(file.getName()).setItems(actions,(d,w) -> {
            if(w == 0) showDetails(file); else if(w == 1) editTextFile(file); else shareFile(file);
        }).show();
    }

    private void showDetails(DocumentFile f) {
        String msg = "Name: " + f.getName() + "\nType: " + f.getType()
                + "\nSize: " + f.length() + " bytes\nModified: " + f.lastModified();
        new AlertDialog.Builder(this).setTitle("File details").setMessage(msg).setPositiveButton("OK",null).show();
    }

    private void createTextFile() {
        if(!ensureScope()) return;
        EditText name = new EditText(this); name.setSingleLine(true); name.setHint("notes.txt");
        EditText body = new EditText(this); body.setHint("Text content"); body.setMinLines(4);
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16),dp(8),dp(16),0); box.addView(name); box.addView(body);
        new AlertDialog.Builder(this).setTitle("Create local text file").setView(box)
                .setPositiveButton("Create",(d,w) -> {
                    String filename = name.getText().toString().trim();
                    if(!LocalScopePolicy.isSafeLeafName(filename)) { setStatus("Invalid file name."); return; }
                    try {
                        DocumentFile created = root.createFile("text/plain",filename);
                        if(created == null) throw new IllegalStateException("Create failed");
                        try(OutputStream out = getContentResolver().openOutputStream(created.getUri(),"wt")) {
                            if(out == null) throw new IllegalStateException("No output stream");
                            out.write(body.getText().toString().getBytes(StandardCharsets.UTF_8));
                        }
                        setStatus("Created: " + filename);
                    } catch(Exception e) { setStatus("Create error: " + e.getMessage()); }
                }).setNegativeButton("Cancel",null).show();
    }

    private void editTextFile(DocumentFile file) {
        if(!LocalScopePolicy.isTextCandidate(file.getType(),file.getName())) {
            setStatus("Only text-like files can be edited here."); return;
        }
        if(file.length() > MAX_EDIT_BYTES) { setStatus("Edit blocked: over 2 MiB."); return; }
        try {
            String text;
            try(InputStream in = getContentResolver().openInputStream(file.getUri());
                ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
                if(in == null) throw new IllegalStateException("No input stream");
                byte[] buf = new byte[8192]; int n;
                while((n = in.read(buf)) != -1) {
                    if(bytes.size() + n > MAX_EDIT_BYTES) throw new IllegalStateException("Over 2 MiB");
                    bytes.write(buf,0,n);
                }
                text = bytes.toString("UTF-8");
            }
            EditText editor = new EditText(this);
            editor.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
            editor.setMinLines(10); editor.setText(text);
            AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Edit " + file.getName())
                    .setView(editor).setPositiveButton("Save",null).setNegativeButton("Cancel",null).create();
            dialog.setOnShowListener(v -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view ->
                    new AlertDialog.Builder(this).setTitle("Confirm overwrite")
                            .setMessage("Replace the contents of " + file.getName() + "?")
                            .setNegativeButton("Cancel",null)
                            .setPositiveButton("Overwrite",(d,w) -> {
                                try(OutputStream out = getContentResolver().openOutputStream(file.getUri(),"wt")) {
                                    if(out == null) throw new IllegalStateException("No output stream");
                                    out.write(editor.getText().toString().getBytes(StandardCharsets.UTF_8));
                                    setStatus("Updated: " + file.getName()); dialog.dismiss();
                                } catch(Exception e) { setStatus("Edit error: " + e.getMessage()); }
                            }).show()));
            dialog.show();
        } catch(Exception e) { setStatus("Cannot open file: " + e.getMessage()); }
    }

    private void shareFile(DocumentFile file) {
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType(file.getType() == null ? "*/*" : file.getType());
        send.putExtra(Intent.EXTRA_STREAM,file.getUri());
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivity(Intent.createChooser(send,"Share file with an app"));
    }

    private void exportReport() {
        if(!ensureScope()) return;
        if(lastReport == null) { setStatus("Run a scan first."); return; }
        try {
            String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date());
            DocumentFile target = root.createFile("application/json","AEGIS_LOCAL_SCAN_REPORT_" + stamp + ".json");
            if(target == null) throw new IllegalStateException("Report create failed");
            try(OutputStream out = getContentResolver().openOutputStream(target.getUri(),"wt")) {
                if(out == null) throw new IllegalStateException("No output stream");
                out.write(lastReport.toString(2).getBytes(StandardCharsets.UTF_8));
            }
            setStatus("Scan report exported into the selected local folder.");
        } catch(Exception e) { setStatus("Export error: " + e.getMessage()); }
    }

    @Override protected void onDestroy() { worker.shutdown(); super.onDestroy(); }
}
