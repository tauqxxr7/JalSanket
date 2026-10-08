// Controlled browser failure/hostile-text fixtures are test-only, never telemetry.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");

(async () => {
  const output = path.join(__dirname, "../artifacts");
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    chromiumSandbox: true,
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1100 },
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto("http://127.0.0.1:8765/", { waitUntil: "networkidle" });
    assert.equal(await page.locator(".queue-row").count(), 5);
    assert.equal(await page.locator("#station-count").textContent(), "5");
    assert.equal(await page.locator("#environment-count").textContent(), "0");
    assert.equal(await page.locator("#flag-count").textContent(), "0");
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
    const assets = await page
      .locator(".legend img")
      .evaluateAll((images) =>
        images.map((i) => ({
          loaded: i.complete && i.naturalWidth > 0,
          width: i.getBoundingClientRect().width,
          height: i.getBoundingClientRect().height,
        })),
      );
    assert.equal(assets.length, 4);
    for (const asset of assets)
      assert.deepEqual(asset, { loaded: true, width: 10, height: 10 });
    await page.screenshot({
      path: path.join(output, "network-desktop.png"),
      fullPage: true,
    });
    await page
      .getByRole("button", {
        name: "Review evidence for Bharosa_1",
        exact: true,
      })
      .click();
    await page.waitForFunction(
      () =>
        document.querySelector("#evidence-title").textContent ===
        "Bharosa_1 · Evidence Trail",
    );
    assert.match(
      await page.locator(".assessment").textContent(),
      /UNCERTAIN — ABSTAIN/,
    );
    assert.match(
      await page.locator(".next-check").textContent(),
      /independent reference measurement/,
    );
    await page
      .getByText("Data quality & detector eligibility", { exact: true })
      .click();
    assert.match(
      await page.locator("#quality").textContent(),
      /FLATLINE: UNAVAILABLE/,
    );
    await page
      .getByText("Source provenance & original evidence rows", { exact: true })
      .click();
    assert.equal(await page.locator("tbody tr").count(), 29);
    await page.screenshot({
      path: path.join(output, "evidence-desktop.png"),
      fullPage: true,
    });
    await page.locator("#station-filter").fill("no-such-station");
    assert.match(
      await page.locator("#queue-list").textContent(),
      /No stations match/,
    );
    await page.locator("#station-filter").fill("Ambhasi");
    assert.equal(await page.locator(".queue-row").count(), 1);
    await page
      .getByRole("button", { name: "Review evidence for Ambhasi", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await page.waitForFunction(
      () =>
        document.querySelector("#evidence-title").textContent ===
        "Ambhasi · Evidence Trail",
    );
    assert.match(
      await page.locator(".assessment").textContent(),
      /UNCERTAIN — ABSTAIN/,
    );
    await page.locator("#station-filter").fill("");
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      ),
      false,
    );
    await page.screenshot({
      path: path.join(output, "network-mobile.png"),
      fullPage: true,
    });
    await page.route("**/api/network", (route) =>
      route.fulfill({ status: 503, json: { detail: "Controlled outage" } }),
    );
    await page.reload({ waitUntil: "networkidle" });
    assert.equal(await page.locator("#error").isVisible(), true);
    assert.equal(await page.locator("#station-count").textContent(), "—");
    assert.match(
      await page.locator("#queue-list").textContent(),
      /Station queue unavailable/,
    );
    await page.unroute("**/api/network");
    await page.getByRole("button", { name: "Retry connection" }).click();
    await page.waitForFunction(
      () => document.querySelectorAll(".queue-row").length === 5,
    );
    await page.route("**/api/stations/*/evidence", (route) =>
      route.fulfill({ status: 500, json: { detail: "Controlled failure" } }),
    );
    await page.locator(".queue-row").first().click();
    await page.waitForFunction(
      () =>
        document.querySelector("#evidence-title").textContent ===
        "Evidence could not be loaded",
    );
    await page.unroute("**/api/stations/*/evidence");
    const original = await (
      await page.request.get("http://127.0.0.1:8765/api/network")
    ).json();
    original.stations[0].label = '<img src=x onerror="window.pwned=true">';
    await page.route("**/api/network", (route) =>
      route.fulfill({ json: original }),
    );
    await page.reload({ waitUntil: "networkidle" });
    assert.match(
      await page.locator(".queue-row").first().textContent(),
      /<img src=x/,
    );
    assert.equal(await page.evaluate(() => window.pwned === undefined), true);
    assert.deepEqual(errors, []);
    const report = {
      status: "PASS",
      checks: [
        "official API → network → evidence preview → abstention → next check",
        "quality and 29 exact source rows",
        "zero candidates never becomes environmental evidence",
        "keyboard station selection",
        "filter and empty state",
        "390px layout has no horizontal overflow",
        "503 source failure and retry",
        "500 evidence failure",
        "hostile label remains inert",
        "four original Figma legend assets at 10×10",
      ],
      page_errors: errors,
      scope: "First screen only; full three-screen E2E pending",
    };
    await fs.writeFile(
      path.join(output, "browser-report.json"),
      JSON.stringify(report, null, 2),
    );
    console.log(JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
