# fix: handle edge cases in geographic aggregation

## Summary
- Fix null handling in district-level rollup
- Add validation for geographic hierarchy consistency
- Handle missing population data gracefully

## Test plan
- [x] Test with missing district
