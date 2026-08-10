package com.example.appium;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.android.options.UiAutomator2Options;
import org.junit.jupiter.api.*;
import org.openqa.selenium.WebElement;

import java.net.URL;
import java.time.Duration;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Minimal Appium + UiAutomator2 smoke test.
 * Integrated with ReportPortal agent for enterprise-grade test automation reporting.
 */
public class SettingsAppTest {

    private static AndroidDriver driver;

    @BeforeAll
    static void setUp() throws Exception {
        UiAutomator2Options options = new UiAutomator2Options()
                .setDeviceName("Medium_Phone_API_36.1")
                .setAppPackage("com.android.settings")
                .setAppActivity("com.android.settings.Settings")
                .setAutomationName("UiAutomator2")
                .setNoReset(true);

        driver = new AndroidDriver(new URL("http://127.0.0.1:4723"), options);
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
    }

    @Test
    void settingsAppOpensAndListsItems() {
        List<WebElement> items = driver.findElements(
                AppiumBy.className("android.widget.TextView")
        );

        assertTrue(items.size() > 0, "We expect the Settings screen to render at least one list item");
    }

    @AfterAll
    static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
