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
 * We drive the native Android Settings app (preinstalled on any emulator,
 * no external app install needed) to prove the automation stack works end to end:
 * Appium server -> UiAutomator2 driver -> emulator -> native UI interaction.
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
        // We locate list items on the Settings home screen by their resource-id.
        List<WebElement> items = driver.findElements(
                AppiumBy.className("android.widget.TextView")
        );

        assertTrue(items.size() > 0, "We expect the Settings screen to render at least one list item");

        // We log the first few visible settings entries as proof of a real interaction.
        items.stream().limit(5).forEach(el -> {
            String text = el.getText();
            if (text != null && !text.isBlank()) {
                System.out.println("Found settings entry: " + text);
            }
        });
    }

    @AfterAll
    static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
