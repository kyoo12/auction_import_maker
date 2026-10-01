// Test JavaScript sanitization and remapping logic
const fs = require('fs');
const assert = require('assert');

// Read app.js and extract the functions to test
const appCode = fs.readFileSync('app.js', 'utf8');

// We can evaluate the functions in a VM context
const vm = require('vm');
const context = {
    console: console,
    Set: Set,
    String: String,
    Number: Number,
    parseInt: parseInt,
    isNaN: isNaN
};
vm.createContext(context);

// Extract the Universal Sanitization Helpers block from app.js
const startMarker = '// Universal Sanitization Helpers';
const endMarker = '// Core conversion logic matching Python pandas script';
const codeSlice = appCode.substring(
    appCode.indexOf(startMarker),
    appCode.indexOf(endMarker)
);

vm.runInContext(codeSlice, context);

const {
    sanitizeMultiLine,
    sanitizeSingleLine,
    sanitizeNumeric,
    convertToBinary,
    sanitizeColumnValue
} = context;

console.log("Testing JS multi-line sanitization...");
// Clean \n preserved
assert.strictEqual(sanitizeMultiLine("Line 1\nLine 2"), "Line 1\nLine 2");
// CRLF -> \n
assert.strictEqual(sanitizeMultiLine("Line 1\r\nLine 2"), "Line 1\nLine 2");
// Isolated \r -> \n
assert.strictEqual(sanitizeMultiLine("Line 1\rLine 2"), "Line 1\nLine 2");
// OpenXML hex entity _x000D_
assert.strictEqual(sanitizeMultiLine("Line 1_x000D_\nLine 2"), "Line 1\nLine 2");
assert.strictEqual(sanitizeMultiLine("Line 1_x000d_Line 2"), "Line 1\nLine 2");
assert.strictEqual(sanitizeMultiLine("Line 1_x000d_\r\nLine 2"), "Line 1\nLine 2");
// Double-escaped OpenXML hex entity _x005F_x000D_
assert.strictEqual(sanitizeMultiLine("Line 1_x005F_x000D_\nLine 2"), "Line 1\nLine 2");
assert.strictEqual(sanitizeMultiLine("Line 1_x005F_x000D_Line 2"), "Line 1\nLine 2");
// Part numbers and text with _xXXXX_ must NEVER be corrupted
assert.strictEqual(sanitizeMultiLine("BATTERY_x2000_MAX"), "BATTERY_x2000_MAX");
assert.strictEqual(sanitizeMultiLine("MODEL_x1234_ABC"), "MODEL_x1234_ABC");
// Unicode line separators \u2028, \u2029 -> \n
assert.strictEqual(sanitizeMultiLine("Line 1\u2028Line 2\u2029Line 3"), "Line 1\nLine 2\nLine 3");
// Unicode spaces -> ' '
assert.strictEqual(sanitizeMultiLine("Word 1\u00A0Word 2\u2003Word 3"), "Word 1 Word 2 Word 3");
// Zero-width chars stripped
assert.strictEqual(sanitizeMultiLine("Zero\u200BWidth\uFEFFBOM\u200DJoiner"), "ZeroWidthBOMJoiner");
// Invisible control chars stripped (preserve \n)
assert.strictEqual(sanitizeMultiLine("Clean\x00Text\x07With\x1FLines\nLine 2"), "CleanTextWithLines\nLine 2");
// Cap at 32,767
assert.strictEqual(sanitizeMultiLine("a".repeat(40000)).length, 32767);
console.log("[OK] JS multi-line sanitization passed!");

console.log("Testing JS single-line sanitization...");
// Internal newlines collapsed to spaces
assert.strictEqual(sanitizeSingleLine("Title Line 1\r\nTitle Line 2"), "Title Line 1 Title Line 2");
assert.strictEqual(sanitizeSingleLine("Title Line 1\nTitle Line 2"), "Title Line 1 Title Line 2");
assert.strictEqual(sanitizeSingleLine("Title Line 1\rTitle Line 2"), "Title Line 1 Title Line 2");
assert.strictEqual(sanitizeSingleLine("Title\u2028Line 2\u2029Line 3"), "Title Line 2 Line 3");
// OpenXML hex entities
assert.strictEqual(sanitizeSingleLine("Brand_x000D_\nName"), "Brand Name");
assert.strictEqual(sanitizeSingleLine("Brand_x005F_x000D_Name"), "Brand Name");
assert.strictEqual(sanitizeSingleLine("Brand_x005F_REV1"), "Brand_REV1");
// Part numbers, model codes, serial numbers with _xXXXX_ must NEVER be corrupted
assert.strictEqual(sanitizeSingleLine("BATTERY_x2000_MAX"), "BATTERY_x2000_MAX");
assert.strictEqual(sanitizeSingleLine("MODEL_x1234_ABC"), "MODEL_x1234_ABC");
assert.strictEqual(sanitizeSingleLine("SN_x0041_123"), "SN_x0041_123");
// Multiple spaces collapsed & trimmed
assert.strictEqual(sanitizeSingleLine("   Brand   with    spaces   "), "Brand with spaces");
// Numbers preserved
assert.strictEqual(sanitizeSingleLine(0), 0);
assert.strictEqual(sanitizeSingleLine(42), 42);
assert.strictEqual(sanitizeSingleLine(150.5), 150.5);
// Strings with leading zeros preserved
assert.strictEqual(sanitizeSingleLine("007"), "007");
// Cap at 32,767
assert.strictEqual(sanitizeSingleLine("b".repeat(40000)).length, 32767);
console.log("[OK] JS single-line sanitization passed!");

console.log("Testing JS numeric sanitization...");
// Numeric 0 preserved (CRITICAL: 0 is not falsy wiped)
assert.strictEqual(sanitizeNumeric(0), 0);
assert.strictEqual(typeof sanitizeNumeric(0), 'number');
// Float preserved
assert.strictEqual(sanitizeNumeric(150.5), 150.5);
assert.strictEqual(typeof sanitizeNumeric(150.5), 'number');
// Numeric strings converted to numbers
assert.strictEqual(sanitizeNumeric("0"), 0);
assert.strictEqual(typeof sanitizeNumeric("0"), 'number');
assert.strictEqual(sanitizeNumeric(" 150.5 "), 150.5);
assert.strictEqual(typeof sanitizeNumeric(" 150.5 "), 'number');
// Booleans are not numeric bids/prices
assert.strictEqual(sanitizeNumeric(true), "");
assert.strictEqual(sanitizeNumeric(false), "");
// Empty / null / undefined / NaN
assert.strictEqual(sanitizeNumeric(""), "");
assert.strictEqual(sanitizeNumeric(null), "");
assert.strictEqual(sanitizeNumeric(undefined), "");
assert.strictEqual(sanitizeNumeric(NaN), "");
// Non-numeric string returned as string
assert.strictEqual(sanitizeNumeric("N/A"), "N/A");
console.log("[OK] JS numeric sanitization passed!");

console.log("Testing JS binary conversion...");
assert.strictEqual(convertToBinary(1), 1);
assert.strictEqual(convertToBinary('1'), 1);
assert.strictEqual(convertToBinary('1.0'), 1);
assert.strictEqual(convertToBinary(1.0), 1);
assert.strictEqual(convertToBinary(true), 1);
assert.strictEqual(convertToBinary('true'), 1);
assert.strictEqual(convertToBinary('True'), 1);
assert.strictEqual(convertToBinary('yes'), 1);
assert.strictEqual(convertToBinary('y'), 1);

assert.strictEqual(convertToBinary(0), "");
assert.strictEqual(convertToBinary('0'), "");
assert.strictEqual(convertToBinary(false), "");
assert.strictEqual(convertToBinary('false'), "");
assert.strictEqual(convertToBinary('no'), "");
assert.strictEqual(convertToBinary(null), "");
assert.strictEqual(convertToBinary(undefined), "");
assert.strictEqual(convertToBinary(""), "");
console.log("[OK] JS binary conversion passed!");

console.log("Testing JS column value routing...");
assert.strictEqual(sanitizeColumnValue('description_en', "Line 1\r\nLine 2"), "Line 1\nLine 2");
assert.strictEqual(sanitizeColumnValue('title_en', "Title 1\r\nTitle 2"), "Title 1 Title 2");
assert.strictEqual(sanitizeColumnValue('starting_bid', 0), 0);
assert.strictEqual(typeof sanitizeColumnValue('starting_bid', 0), 'number');
assert.strictEqual(sanitizeColumnValue('starting_bid', " 150.5 "), 150.5);
assert.strictEqual(typeof sanitizeColumnValue('starting_bid', " 150.5 "), 'number');
assert.strictEqual(sanitizeColumnValue('needs_manual_allocation', '1'), 1);
assert.strictEqual(sanitizeColumnValue('is_spotlight', 'true'), 1);
assert.strictEqual(sanitizeColumnValue('attribute-serial_number', '00042'), '00042');
console.log("[OK] JS column value routing passed!");

console.log("\nALL JAVASCRIPT TESTS PASSED SUCCESSFULLY!");
