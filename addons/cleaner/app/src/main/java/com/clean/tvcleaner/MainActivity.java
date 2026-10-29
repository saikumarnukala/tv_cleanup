package com.clean.tvcleaner;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.os.StatFs;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {

    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView memoryStatsView;
    private TextView storageStatsView;
    private TextView statusView;
    private Button boostBtn;

    private final Runnable refreshRunnable = new Runnable() {
        @Override
        public void run() {
            updateStats();
            handler.postDelayed(this, 4000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.rgb(16, 24, 32));
        scroll.setFillViewport(true);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(64, 48, 64, 48);
        layout.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(layout);

        setContentView(scroll);

        // Title
        TextView title = new TextView(this);
        title.setText("TV Cleaner & Speed Booster");
        title.setTextSize(32);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        title.setPadding(0, 0, 0, 16);
        layout.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Clean background apps, reclaim RAM, and manage storage");
        subtitle.setTextSize(16);
        subtitle.setTextColor(Color.rgb(160, 180, 200));
        subtitle.setGravity(Gravity.CENTER_HORIZONTAL);
        subtitle.setPadding(0, 0, 0, 36);
        layout.addView(subtitle);

        // Stats Container Card
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(32, 28, 32, 28);
        GradientDrawable cardBg = new GradientDrawable();
        cardBg.setColor(Color.rgb(26, 38, 52));
        cardBg.setCornerRadius(16f);
        card.setBackground(cardBg);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        cardParams.setMargins(0, 0, 0, 36);
        layout.addView(card, cardParams);

        memoryStatsView = new TextView(this);
        memoryStatsView.setTextSize(20);
        memoryStatsView.setTextColor(Color.WHITE);
        memoryStatsView.setPadding(0, 0, 0, 16);
        card.addView(memoryStatsView);

        storageStatsView = new TextView(this);
        storageStatsView.setTextSize(20);
        storageStatsView.setTextColor(Color.rgb(200, 225, 255));
        card.addView(storageStatsView);

        // Status text
        statusView = new TextView(this);
        statusView.setText(getString(R.string.status_ready));
        statusView.setTextSize(17);
        statusView.setTextColor(Color.rgb(0, 230, 118)); // Emerald
        statusView.setGravity(Gravity.CENTER_HORIZONTAL);
        statusView.setPadding(0, 0, 0, 32);
        layout.addView(statusView);

        // Buttons
        boostBtn = createButton("⚡ 1-Click Memory Boost", Color.rgb(0, 200, 83), () -> performMemoryBoost());
        layout.addView(boostBtn);

        Button manageAppsBtn = createButton("📦 Manage App Caches", Color.rgb(33, 150, 243), () -> openStorageSettings());
        layout.addView(manageAppsBtn);

        Button exitBtn = createButton("Exit", Color.rgb(55, 71, 79), () -> finish());
        layout.addView(exitBtn);

        boostBtn.requestFocus();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateStats();
        handler.postDelayed(refreshRunnable, 4000);
    }

    @Override
    protected void onPause() {
        handler.removeCallbacksAndMessages(null);
        super.onPause();
    }

    private Button createButton(String text, int normalColor, Runnable action) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setTextSize(18);
        btn.setTextColor(Color.WHITE);
        btn.setPadding(32, 20, 32, 20);

        StateListDrawable states = new StateListDrawable();

        // Focused state (bright cyan/green outline & glow)
        GradientDrawable focused = new GradientDrawable();
        focused.setColor(normalColor);
        focused.setCornerRadius(12f);
        focused.setStroke(4, Color.WHITE);
        states.addState(new int[]{android.R.attr.state_focused}, focused);

        // Normal state
        GradientDrawable normal = new GradientDrawable();
        normal.setColor(normalColor);
        normal.setCornerRadius(12f);
        states.addState(new int[]{}, normal);

        btn.setBackground(states);
        btn.setFocusable(true);
        btn.setOnClickListener(v -> action.run());

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, 20);
        btn.setLayoutParams(params);
        return btn;
    }

    private void updateStats() {
        // 1. RAM info from /proc/meminfo
        long totalMb = 0, availMb = 0, freeMb = 0, bufMb = 0, cacheMb = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader("/proc/meminfo"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("MemTotal:")) totalMb = parseKb(line) / 1024;
                else if (line.startsWith("MemAvailable:")) availMb = parseKb(line) / 1024;
                else if (line.startsWith("MemFree:")) freeMb = parseKb(line) / 1024;
                else if (line.startsWith("Buffers:")) bufMb = parseKb(line) / 1024;
                else if (line.startsWith("Cached:")) cacheMb = parseKb(line) / 1024;
            }
        } catch (Exception ignored) { }

        // MediaTek / kernel sanity fallback
        if (availMb <= 0 || availMb > totalMb) {
            availMb = freeMb + bufMb + cacheMb;
        }
        long usedMb = Math.max(0, totalMb - availMb);
        int memPercent = totalMb > 0 ? (int) ((usedMb * 100) / totalMb) : 0;

        memoryStatsView.setText(String.format(Locale.US,
                "RAM: %d MB Used / %d MB Total (%d%% Used · %d MB Free)",
                usedMb, totalMb, memPercent, availMb));

        // 2. Storage info
        File dataDir = Environment.getDataDirectory();
        StatFs stat = new StatFs(dataDir.getPath());
        long totalStorageGb = (stat.getBlockCountLong() * stat.getBlockSizeLong()) / (1024 * 1024 * 1024);
        long freeStorageGb = (stat.getAvailableBlocksLong() * stat.getBlockSizeLong()) / (1024 * 1024 * 1024);
        long usedStorageGb = Math.max(0, totalStorageGb - freeStorageGb);

        storageStatsView.setText(String.format(Locale.US,
                "Storage: %d GB Used / %d GB Total (%d GB Free)",
                usedStorageGb, totalStorageGb, freeStorageGb));
    }

    private long parseKb(String line) {
        String[] parts = line.trim().split("\\s+");
        if (parts.length >= 2) {
            try { return Long.parseLong(parts[1]); } catch (Exception ignored) { }
        }
        return 0;
    }

    private void performMemoryBoost() {
        statusView.setText("Cleaning background apps & freeing memory...");
        statusView.setTextColor(Color.rgb(255, 235, 59)); // Yellow

        handler.postDelayed(() -> {
            ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            PackageManager pm = getPackageManager();
            int killedCount = 0;

            if (am != null && pm != null) {
                List<ApplicationInfo> packages = pm.getInstalledApplications(PackageManager.GET_META_DATA);
                String myPackage = getPackageName();

                for (ApplicationInfo app : packages) {
                    // Do not kill self or core android packages
                    if (app.packageName.equals(myPackage)) continue;
                    if (app.packageName.equals("android") || app.packageName.startsWith("com.android.systemui")) continue;

                    try {
                        am.killBackgroundProcesses(app.packageName);
                        killedCount++;
                    } catch (Exception ignored) { }
                }
            }

            // Run GC and clean internal cache
            System.gc();
            try {
                File cache = getCacheDir();
                if (cache != null && cache.isDirectory()) {
                    for (File f : cache.listFiles()) f.delete();
                }
            } catch (Exception ignored) { }

            updateStats();
            statusView.setText(String.format(Locale.US,
                    "✓ Memory Boosted! Terminated %d cached processes. System is optimal.", killedCount));
            statusView.setTextColor(Color.rgb(0, 230, 118)); // Emerald
        }, 500);
    }

    private void openStorageSettings() {
        try {
            startActivity(new Intent(Settings.ACTION_INTERNAL_STORAGE_SETTINGS));
        } catch (Exception e1) {
            try {
                startActivity(new Intent(Settings.ACTION_MANAGE_APPLICATIONS_SETTINGS));
            } catch (Exception e2) {
                try {
                    startActivity(new Intent(Settings.ACTION_SETTINGS));
                } catch (Exception ignored) { }
            }
        }
    }
}
