package org.jefeaguila.honorbridge;

import org.junit.Test;
import static org.junit.Assert.*;

public class LocalScopePolicyTest {
    @Test public void acceptsOnlyOnDeviceStorageProvider() {
        assertTrue(LocalScopePolicy.isLocalAuthority("com.android.externalstorage.documents"));
        assertFalse(LocalScopePolicy.isLocalAuthority("com.google.android.apps.docs.storage"));
        assertFalse(LocalScopePolicy.isLocalAuthority("com.dropbox.android.filecache"));
        assertFalse(LocalScopePolicy.isLocalAuthority("com.android.providers.media.documents"));
    }
    @Test public void rejectsPathTraversalNames() {
        assertTrue(LocalScopePolicy.isSafeLeafName("notes.txt"));
        assertFalse(LocalScopePolicy.isSafeLeafName("../notes.txt"));
        assertFalse(LocalScopePolicy.isSafeLeafName("folder/notes.txt"));
        assertFalse(LocalScopePolicy.isSafeLeafName("folder\\notes.txt"));
        assertFalse(LocalScopePolicy.isSafeLeafName(""));
    }
    @Test public void limitsEditsToTextFiles() {
        assertTrue(LocalScopePolicy.isTextCandidate("text/plain","notes.txt"));
        assertTrue(LocalScopePolicy.isTextCandidate("application/json","settings.json"));
        assertFalse(LocalScopePolicy.isTextCandidate("application/octet-stream","archive.bin"));
    }
}
