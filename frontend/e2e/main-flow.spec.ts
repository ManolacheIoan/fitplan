import { expect, test } from "@playwright/test";

test("register → onboarding → plan → log workout → log food → progress", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  // Register (consent is part of the form)
  await page.goto("/inregistrare");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Parolă").fill("parola-sigura-123");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Creează cont" }).click();

  // Onboarding questionnaire
  await expect(page).toHaveURL(/\/profil\/chestionar/);
  await page.getByLabel("Nume").fill("Ana");
  await page
    .getByRole("group", { name: /Sex biologic/ })
    .getByText("Feminin")
    .click();
  await page.getByLabel("Data nașterii").fill("1995-05-20");
  await page.getByLabel("Înălțime (cm)").fill("168");
  await page.getByLabel("Greutate (kg)").fill("70");
  await page.getByRole("group", { name: "Obiectiv" }).getByText("Slăbire").click();
  await page
    .getByRole("group", { name: /Zile de antrenament/ })
    .getByText("3", { exact: true })
    .click();
  await page.getByRole("group", { name: "Experiență" }).getByText("Începător").click();
  await page.getByRole("button", { name: "Continuă" }).click();

  // Safety screening: all "no"
  await expect(page).toHaveURL(/\/profil\/screening/);
  for (const group of await page.getByRole("group").all()) {
    await group.getByText("Nu", { exact: true }).click();
  }
  await page.getByRole("button", { name: "Trimite" }).click();

  // Today: targets are shown as approximate estimates
  await expect(page).toHaveURL(/\/azi/);
  await expect(page.getByText("Estimare aproximativă")).toBeVisible();
  await expect(page.getByText(/Informațiile sunt orientative/)).toBeVisible();

  // Plan
  await page.getByRole("link", { name: "Plan", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Ziua 1/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Ziua 3/ })).toBeVisible();

  // Log a workout
  await page.getByRole("link", { name: "Azi", exact: true }).click();
  await page.getByRole("button", { name: "Începe antrenamentul" }).click();
  await expect(page).toHaveURL(/\/antrenament\?id=\d+/);
  const firstExercise = page.locator("form").first();
  await firstExercise.getByLabel("Greutate (kg)").fill("20");
  await firstExercise.getByLabel("Repetări").fill("10");
  await firstExercise.getByRole("button", { name: "+ Serie" }).click();
  await expect(page.getByText("Seria 1: 20 kg × 10")).toBeVisible();
  await page.getByRole("button", { name: "Termină antrenamentul" }).click();
  await expect(page).toHaveURL(/\/antrenament\/istoric/);
  await expect(page.getByText(/1 serii · 200 kg volum/)).toBeVisible();

  // Log food
  await page.getByRole("link", { name: "Mâncare" }).click();
  await page.getByLabel("Caută aliment").fill("ovaz");
  await page.getByRole("button", { name: /Fulgi de ovăz/ }).click();
  await page.getByLabel("Cantitate (g)").fill("50");
  await page.getByRole("button", { name: "Adaugă", exact: true }).click();
  await expect(page.getByText("50 g · 189,5 kcal")).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "Calorii" })).toBeVisible();

  // Progress
  await page.getByRole("link", { name: "Progres" }).click();
  await page.getByLabel("Greutate (kg)").fill("69.5");
  await page.getByRole("button", { name: "Salvează greutatea" }).click();
  await expect(page.getByRole("status").filter({ hasText: /salvată|actualizate/ })).toBeVisible();
  await expect(page.getByRole("img", { name: /Grafic greutate/ })).toBeVisible();
  await expect(page.getByRole("img", { name: /Grafic volum/ })).toBeVisible();
});

test("screening with a 'yes' answer shows only the professional-advice page", async ({ page }) => {
  await page.goto("/inregistrare");
  await page.getByLabel("Email").fill(`e2e-refer-${Date.now()}@example.com`);
  await page.getByLabel("Parolă").fill("parola-sigura-123");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Creează cont" }).click();

  await page.getByLabel("Nume").fill("Ion");
  await page
    .getByRole("group", { name: /Sex biologic/ })
    .getByText("Masculin")
    .click();
  await page.getByLabel("Data nașterii").fill("1990-01-10");
  await page.getByLabel("Înălțime (cm)").fill("180");
  await page.getByLabel("Greutate (kg)").fill("85");
  await page.getByRole("group", { name: "Obiectiv" }).getByText("Menținere").click();
  await page
    .getByRole("group", { name: /Zile de antrenament/ })
    .getByText("4", { exact: true })
    .click();
  await page.getByRole("group", { name: "Experiență" }).getByText("Avansat").click();
  await page.getByRole("button", { name: "Continuă" }).click();

  const groups = await page.getByRole("group").all();
  for (const [index, group] of groups.entries()) {
    await group.getByText(index === 3 ? "Da" : "Nu", { exact: true }).click();
  }
  await page.getByRole("button", { name: "Trimite" }).click();
  await expect(page).toHaveURL(/\/recomandare/);
  await expect(page.getByText(/discuți mai întâi cu un medic/)).toBeVisible();

  // The generated features stay unavailable.
  await page.goto("/plan");
  await expect(page).toHaveURL(/\/recomandare/);
});
