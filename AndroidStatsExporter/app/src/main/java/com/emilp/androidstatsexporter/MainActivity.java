package com.emilp.androidstatsexporter;

import android.Manifest;
import android.app.usage.UsageStats;
import android.app.usage.UsageStatsManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.Calendar;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "AndroidStatsExporter";
    private static final int MY_PERMISSIONS_REQUEST_PACKAGE_USAGE_STATS_CODE = 1112;
    private final ActivityResultLauncher<String> requestPermissionLauncher =
            registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
                if (isGranted) {
                    Log.d(TAG, "permission GRANTED");
                    // Permission is granted. Continue the action or workflow in your
                    // app.
                } else {
                    Log.d(TAG, "permission NOT GRANTED");
                    // Explain to the user that the feature is unavailable because the
                    // features requires a permission that the user has denied. At the
                    // same time, respect the user's decision. Don't link to system
                    // settings in an effort to convince the user to change their
                    // decision.
                }
            });

    Button mOpenUsageSettingButton;


    private final int numRequests = 0;
    private boolean mUsageStatisticsPermissionGranted = false;
    private UsageStatsManager mUsageStatsManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        checkPermission();

        mOpenUsageSettingButton = findViewById(R.id.button_open_usage_setting);

    }

    public List<UsageStats> getUsageStatistics(int intervalType) {
        // Get the app statistics since one year ago from the current time.
        Calendar cal = Calendar.getInstance();
        cal.add(Calendar.YEAR, -1);

        List<UsageStats> queryUsageStats = null;
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
            queryUsageStats = mUsageStatsManager
                    .queryUsageStats(intervalType, cal.getTimeInMillis(),
                            System.currentTimeMillis());
        }

        if (queryUsageStats != null && queryUsageStats.size() == 0) {
            Log.i(TAG, "The user may not allow the access to apps usage. ");
            Toast.makeText(this,
                    "There is no access to usage statistics given for the app.",
                    Toast.LENGTH_LONG).show();
            mOpenUsageSettingButton.setVisibility(View.VISIBLE);
            mOpenUsageSettingButton.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    startActivity(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS));
                }
            });
        }
        return queryUsageStats;
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            mUsageStatsManager = (UsageStatsManager) this.getSystemService(this.getApplicationContext().USAGE_STATS_SERVICE);
            List<UsageStats> usageStats = getUsageStatistics(UsageStatsManager.INTERVAL_DAILY);
            Log.d(TAG, String.format("%d", usageStats.size()));
            Log.d(TAG, String.format("%s", usageStats.get(0).getPackageName()));
            Log.d(TAG, String.format("%d", usageStats.get(0).getTotalTimeInForeground()));
//            Calendar cal = Calendar.getInstance();
//            cal.add(Calendar.YEAR, -1);
//            List<UsageStats> queryUsageStats = mUsageStatsManager
//                    .queryUsageStats(UsageStatsManager.INTERVAL_DAILY, cal.getTimeInMillis(),
//                            System.currentTimeMillis());
        }
    }

    private void checkPermission() {
        if (ContextCompat.checkSelfPermission(this.getApplicationContext(),
                Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED) {
            mUsageStatisticsPermissionGranted = true;
        } else {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.PACKAGE_USAGE_STATS},
                    MY_PERMISSIONS_REQUEST_PACKAGE_USAGE_STATS_CODE);
        }
    }

}