package org.jefeaguila.honorbridge;

final class LocalScopePolicy {
    private LocalScopePolicy() {}

    static boolean isLocalAuthority(String authority) {
        return "com.android.externalstorage.documents".equals(authority);
    }

    static boolean isSafeLeafName(String name) {
        if (name == null) return false;
        String value = name.trim();
        return !value.isEmpty() && !value.equals(".") && !value.equals("..")
                && !value.contains("/") && !value.contains("\\") && value.length() <= 120;
    }

    static boolean isTextCandidate(String mimeType, String name) {
        if (mimeType != null && (mimeType.startsWith("text/")
                || mimeType.equals("application/json")
                || mimeType.equals("application/xml"))) return true;
        String lower = name == null ? "" : name.toLowerCase(java.util.Locale.ROOT);
        return lower.endsWith(".txt") || lower.endsWith(".md") || lower.endsWith(".csv")
                || lower.endsWith(".json") || lower.endsWith(".xml") || lower.endsWith(".log")
                || lower.endsWith(".yaml") || lower.endsWith(".yml");
    }
}
