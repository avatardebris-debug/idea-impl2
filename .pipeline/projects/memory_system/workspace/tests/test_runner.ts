/**
 * Test Runner for Memory System
 * Entry point for running all tests
 */

import * as palaceTemplatesTests from './palaceTemplates.test';
import * as palaceExportImportTests from './palaceExportImport.test';
import * as progressTrackingTests from './progressTracking.test';
import * as spatialExerciseTests from './SpatialExercise.test';
import * as accuracyAnalyticsTests from '../src/utils/accuracyAnalytics.test';

/**
 * Run all test suites
 */
export const runAllTests = async (): Promise<{
  passed: number;
  failed: number;
  total: number;
  results: TestResult[];
}> => {
  const results: TestResult[] = [];
  let passed = 0;
  let failed = 0;

  // Run palace templates tests
  const templatesResult = await runTestSuite('Palace Templates', palaceTemplatesTests);
  results.push(templatesResult);
  passed += templatesResult.passed;
  failed += templatesResult.failed;

  // Run export/import tests
  const exportImportResult = await runTestSuite('Export/Import', palaceExportImportTests);
  results.push(exportImportResult);
  passed += exportImportResult.passed;
  failed += exportImportResult.failed;

  // Run progress tracking tests
  const progressResult = await runTestSuite('Progress Tracking', progressTrackingTests);
  results.push(progressResult);
  passed += progressResult.passed;
  failed += progressResult.failed;

  // Run spatial exercise tests
  const spatialResult = await runTestSuite('Spatial Exercise', spatialExerciseTests);
  results.push(spatialResult);
  passed += spatialResult.passed;
  failed += spatialResult.failed;

  // Run accuracy analytics tests
  const accuracyResult = await runTestSuite('Accuracy Analytics', accuracyAnalyticsTests);
  results.push(accuracyResult);
  passed += accuracyResult.passed;
  failed += accuracyResult.failed;

  return {
    passed,
    failed,
    total: passed + failed,
    results,
  };
};

/**
 * Run a single test suite
 */
async function runTestSuite(
  suiteName: string,
  testModule: any
): Promise<TestResult> {
  const suiteResult: TestResult = {
    name: suiteName,
    passed: 0,
    failed: 0,
    tests: [],
  };

  // Get all test functions from the module
  const testFunctions = Object.keys(testModule)
    .filter((key) => key.startsWith('describe') || key.startsWith('it'))
    .map((key) => ({
      name: key,
      fn: testModule[key],
    }));

  for (const test of testFunctions) {
    try {
      await test.fn();
      suiteResult.passed++;
      suiteResult.tests.push({
        name: test.name,
        status: 'passed',
        duration: 0,
      });
    } catch (error) {
      suiteResult.failed++;
      suiteResult.tests.push({
        name: test.name,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        duration: 0,
      });
    }
  }

  return suiteResult;
}

/**
 * Test result interface
 */
export interface TestResult {
  name: string;
  passed: number;
  failed: number;
  tests: Array<{
    name: string;
    status: 'passed' | 'failed';
    error?: string;
    duration: number;
  }>;
}

/**
 * Print test results to console
 */
export const printResults = (results: {
  passed: number;
  failed: number;
  total: number;
  results: TestResult[];
}): void => {
  console.log('\n=== Test Results ===');
  console.log(`Total: ${results.total}`);
  console.log(`Passed: ${results.passed}`);
  console.log(`Failed: ${results.failed}`);
  console.log('');

  for (const suite of results.results) {
    console.log(`\n${suite.name}:`);
    console.log(`  Passed: ${suite.passed}`);
    console.log(`  Failed: ${suite.failed}`);

    for (const test of suite.tests) {
      const status = test.status === 'passed' ? '✓' : '✗';
      const prefix = test.status === 'passed' ? '  ' : '  ERROR: ';
      console.log(`  ${status} ${test.name}`);
      if (test.error) {
        console.log(`  ${prefix}${test.error}`);
      }
    }
  }

  console.log('\n===================\n');
};

/**
 * Run tests and print results
 */
export const runAndPrintTests = async (): Promise<void> => {
  const results = await runAllTests();
  printResults(results);

  if (results.failed > 0) {
    throw new Error(`${results.failed} tests failed`);
  }
};

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAndPrintTests().catch((error) => {
    console.error('Test run failed:', error);
    process.exit(1);
  });
}
