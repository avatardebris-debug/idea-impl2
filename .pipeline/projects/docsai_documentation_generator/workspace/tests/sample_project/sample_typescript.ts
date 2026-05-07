/**
 * A sample TypeScript module for end-to-end testing.
 */

/**
 * Greet a person by name.
 * @param name - The person's name.
 * @returns A greeting string.
 */
export function greet(name: string): string {
    return `Hello, ${name}!`;
}

/**
 * A simple calculator class.
 */
export class Calculator {
    private value: number;

    /**
     * Initialize the calculator.
     * @param initialValue - The starting value.
     */
    constructor(initialValue: number = 0) {
        this.value = initialValue;
    }

    /**
     * Add a number to the current value.
     * @param number - The number to add.
     * @returns The new value.
     */
    public add(number: number): number {
        this.value += number;
        return this.value;
    }

    /**
     * Multiply the current value by a factor.
     * @param factor - The multiplication factor.
     * @returns The new value.
     */
    public multiply(factor: number): number {
        this.value *= factor;
        return this.value;
    }
}

/**
 * Compute the sum of an array of numbers.
 * @param numbers - Array of numeric values.
 * @returns The sum.
 */
export function computeSum(numbers: number[]): number {
    return numbers.reduce((acc, n) => acc + n, 0);
}

/**
 * Interface for a point in 2D space.
 */
export interface Point {
    x: number;
    y: number;
}
