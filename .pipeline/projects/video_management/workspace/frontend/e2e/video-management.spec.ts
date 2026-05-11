import { test, expect } from '@playwright/test';

test.describe('Video Management Platform', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Video List Page', () => {
    test('should display the video list page', async ({ page }) => {
      await expect(page.getByText('Videos')).toBeVisible();
      await expect(page.getByText('+ Add Video')).toBeVisible();
    });

    test('should display videos in a grid', async ({ page }) => {
      await expect(page.locator('.video-grid')).toBeVisible();
    });

    test('should display video cards', async ({ page }) => {
      await expect(page.locator('.video-card')).toHaveCount(2);
    });

    test('should display video title', async ({ page }) => {
      await expect(page.getByText('Test Video 1')).toBeVisible();
      await expect(page.getByText('Test Video 2')).toBeVisible();
    });

    test('should display video description', async ({ page }) => {
      await expect(page.getByText('Description 1')).toBeVisible();
      await expect(page.getByText('Description 2')).toBeVisible();
    });

    test('should display status badges', async ({ page }) => {
      await expect(page.getByText('draft')).toBeVisible();
      await expect(page.getByText('published')).toBeVisible();
    });

    test('should display tags', async ({ page }) => {
      await expect(page.getByText('#test')).toBeVisible();
      await expect(page.getByText('#video')).toBeVisible();
    });

    test('should have edit button on each video', async ({ page }) => {
      const editButtons = page.locator('.video-card .btn-secondary');
      await expect(editButtons).toHaveCount(2);
    });

    test('should have delete button on each video', async ({ page }) => {
      const deleteButtons = page.locator('.video-card .btn-danger');
      await expect(deleteButtons).toHaveCount(2);
    });

    test('should navigate to create video page', async ({ page }) => {
      await page.getByText('+ Add Video').click();
      await expect(page).toHaveURL('/videos/new');
    });

    test('should navigate to edit video page', async ({ page }) => {
      await page.locator('.video-card').first().getByText('Edit').click();
      await expect(page).toHaveURL(/\/videos\/\d+\/edit/);
    });

    test('should search videos', async ({ page }) => {
      await page.getByPlaceholder('Search videos...').fill('Test Video 1');
      await expect(page.getByText('Test Video 1')).toBeVisible();
      await expect(page.getByText('Test Video 2')).not.toBeVisible();
    });

    test('should filter by status', async ({ page }) => {
      await page.getByRole('combobox').selectOption('published');
      await expect(page.getByText('Test Video 1')).not.toBeVisible();
      await expect(page.getByText('Test Video 2')).toBeVisible();
    });

    test('should show pagination', async ({ page }) => {
      await expect(page.getByText(/Page \d+ of/)).toBeVisible();
    });

    test('should navigate to next page', async ({ page }) => {
      await page.getByRole('button', { name: 'Next' }).click();
      await expect(page.getByText(/Page 2 of/)).toBeVisible();
    });
  });

  test.describe('Video Form Page', () => {
    test('should display the create video form', async ({ page }) => {
      await page.goto('/videos/new');
      await expect(page.getByText('Create Video')).toBeVisible();
    });

    test('should display form fields', async ({ page }) => {
      await page.goto('/videos/new');
      await expect(page.getByLabel('Title')).toBeVisible();
      await expect(page.getByLabel('Description')).toBeVisible();
      await expect(page.getByLabel('Status')).toBeVisible();
    });

    test('should create a video', async ({ page }) => {
      await page.goto('/videos/new');
      await page.getByLabel('Title').fill('New Video');
      await page.getByLabel('Description').fill('New Description');
      await page.getByLabel('Status').selectOption('published');
      await page.getByText('Create Video').click();
      await expect(page).toHaveURL('/videos');
    });

    test('should validate title is required', async ({ page }) => {
      await page.goto('/videos/new');
      await page.getByText('Create Video').click();
      await expect(page.getByText('Title is required')).toBeVisible();
    });

    test('should display the edit video form', async ({ page }) => {
      await page.goto('/videos/1/edit');
      await expect(page.getByText('Update Video')).toBeVisible();
    });

    test('should pre-fill form when editing', async ({ page }) => {
      await page.goto('/videos/1/edit');
      await expect(page.getByLabel('Title')).toHaveValue('Test Video');
    });

    test('should update a video', async ({ page }) => {
      await page.goto('/videos/1/edit');
      await page.getByLabel('Title').fill('Updated Video');
      await page.getByText('Update Video').click();
      await expect(page).toHaveURL('/videos');
    });

    test('should cancel and navigate back', async ({ page }) => {
      await page.goto('/videos/new');
      await page.getByText('Cancel').click();
      await expect(page).toHaveURL('/videos');
    });
  });

  test.describe('Fields Page', () => {
    test('should display the fields page', async ({ page }) => {
      await page.goto('/fields');
      await expect(page.getByText('Fields')).toBeVisible();
    });

    test('should display table selector', async ({ page }) => {
      await page.goto('/fields');
      await expect(page.getByLabel('Select table')).toBeVisible();
    });

    test('should display fields', async ({ page }) => {
      await page.goto('/fields');
      await expect(page.getByText('title')).toBeVisible();
      await expect(page.getByText('description')).toBeVisible();
    });

    test('should create a field', async ({ page }) => {
      await page.goto('/fields');
      await page.getByLabel('Field name').fill('new_field');
      await page.getByLabel('Field type').selectOption('TEXT');
      await page.getByText('Add Field').click();
      await expect(page.getByText('new_field')).toBeVisible();
    });

    test('should delete a field', async ({ page }) => {
      await page.goto('/fields');
      await page.locator('.field-item').first().getByText('Delete').click();
      await expect(page.getByText('new_field')).not.toBeVisible();
    });

    test('should switch tables', async ({ page }) => {
      await page.goto('/fields');
      await page.getByLabel('Select table').selectOption('2');
      await expect(page.getByText('content')).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test('should navigate between pages', async ({ page }) => {
      await page.goto('/');
      await page.getByText('Videos').click();
      await expect(page).toHaveURL('/videos');
      
      await page.getByText('Fields').click();
      await expect(page).toHaveURL('/fields');
    });

    test('should highlight active navigation item', async ({ page }) => {
      await page.goto('/videos');
      await expect(page.getByText('Videos')).toHaveClass(/active/);
      
      await page.getByText('Fields').click();
      await expect(page.getByText('Fields')).toHaveClass(/active/);
    });
  });

  test.describe('Error Handling', () => {
    test('should show error message on API failure', async ({ page }) => {
      await page.goto('/videos');
      // Simulate API error
      await page.evaluate(() => {
        window.fetch = () => Promise.reject(new Error('API Error'));
      });
      await page.reload();
      await expect(page.getByText('API Error')).toBeVisible();
    });

    test('should show validation errors', async ({ page }) => {
      await page.goto('/videos/new');
      await page.getByText('Create Video').click();
      await expect(page.getByText('Title is required')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should display correctly on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await expect(page.locator('.video-grid')).toBeVisible();
    });

    test('should display correctly on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');
      await expect(page.locator('.video-grid')).toBeVisible();
    });

    test('should display correctly on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto('/');
      await expect(page.locator('.video-grid')).toBeVisible();
    });
  });
});
