import { test, expect } from '@playwright/test';

test.describe('TrueLend End-to-End User Journeys', () => {
  test('Customer login and loan application submission', async ({ page }) => {
    await page.goto('/');

    // 1. Login Screen
    await expect(page.getByTestId('login-container')).toBeVisible();
    await page.getByTestId('token-select').selectOption('demo-customer-1');
    await page.getByTestId('login-submit-button').click();

    // 2. Navigation bar visible for Customer
    await expect(page.getByTestId('current-user-info')).toContainText('cust-001 (CUSTOMER)');
    await expect(page.getByTestId('nav-tab-apply')).toBeVisible();
    await expect(page.getByTestId('nav-tab-track')).toBeVisible();
    await expect(page.getByTestId('nav-tab-repay')).toBeVisible();

    // 3. Fill and submit application
    await page.getByTestId('applicant-name-input').fill('E2E Test Applicant');
    await page.getByTestId('applicant-income-input').fill('80000.00');
    await page.getByTestId('applicant-pan-input').fill('TESTP9999X');
    await page.getByTestId('applicant-aadhaar-input').fill('999900000099');
    await page.getByTestId('loan-amount-input').fill('200000.00');
    await page.getByTestId('loan-tenure-input').fill('36');

    await page.getByTestId('apply-submit-button').click();

    // 4. Verify application result
    await expect(page.getByTestId('apply-result')).toBeVisible();
    await expect(page.getByTestId('apply-result-id')).toBeVisible();
  });

  test('Underwriter login and workbench queue review', async ({ page }) => {
    await page.goto('/');

    // Login as Underwriter
    await page.getByTestId('token-select').selectOption('demo-underwriter-1');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByTestId('current-user-info')).toContainText('uw-001 (UNDERWRITER)');
    await expect(page.getByTestId('nav-tab-workbench')).toBeVisible();
    await expect(page.getByTestId('workbench-view')).toBeVisible();
    await expect(page.getByTestId('queue-table')).toBeVisible();
  });

  test('Admin login, portfolio dashboard, and policy editor', async ({ page }) => {
    await page.goto('/');

    // Login as Admin
    await page.getByTestId('token-select').selectOption('demo-admin-1');
    await page.getByTestId('login-submit-button').click();

    await expect(page.getByTestId('current-user-info')).toContainText('adm-001 (ADMIN)');
    await expect(page.getByTestId('nav-tab-dashboard')).toBeVisible();
    await expect(page.getByTestId('nav-tab-policy-editor')).toBeVisible();
    await expect(page.getByTestId('dashboard-view')).toBeVisible();
    await expect(page.getByTestId('metric-total-apps')).toBeVisible();

    // Switch to Policy Editor tab
    await page.getByTestId('nav-tab-policy-editor').click();
    await expect(page.getByTestId('policy-editor-view')).toBeVisible();
    await expect(page.getByTestId('change-note-input')).toBeVisible();
  });
});
