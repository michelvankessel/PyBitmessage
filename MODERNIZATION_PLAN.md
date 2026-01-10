# PyBitmessage Modernization Plan

**Created:** 2026-01-10 | **Status:** Active

---

## Executive Summary

| Category | Total Count | Priority |
|----------|-------------|----------|
| Type Safety (type: ignore) | 7 violations | 🔴 P0 |
| Pathlib Migration (os.path) | 150 occurrences | 🟡 P1 |
| F-string Conversion (.format()) | 96 occurrences | 🟡 P1 |
| Type Hints (partial coverage) | ~100 files | 🟢 P2 |

---

## Phase 1: Critical Type Safety (Week 1)

### Goal: Eliminate all `type: ignore` violations

| File | Line | Issue | Effort |
|------|------|-------|--------|
| `api.py` | 238 | Import type ignore | 2h |
| `depends.py` | 189, 261 | Cryptography imports | 3h |
| `bmconfigparser.py` | 202 | readfp assignment | 2h |
| `mockbm/kivy_main.py` | 10 | Import | 1h |
| `knownnodes.py` | 19 | Peer assignment | 2h |

**Total Effort:** ~10 hours

**Approach:**
1. Create type stubs for external modules
2. Fix underlying type issues
3. Add proper annotations

---

## Phase 2: Pathlib Migration (Weeks 2-4)

### Goal: Replace 150 `os.path` usages with `pathlib.Path`

#### Priority 1: High-Impact Files

| File | Count | Risk | Effort |
|------|-------|------|--------|
| `paths.py` | ~8 | High | 4h |
| `storage/filesystem.py` | 13 | High | 6h |
| `bitmessageqt/mainwindow.py` | 13 | Medium | 8h |
| `bitmessagekivy/mpybit.py` | 20 | Medium | 10h |

#### Priority 2: Medium-Impact Files

| File | Count | Effort |
|------|-------|--------|
| `bitmessagecli.py` | ~6 | 3h |
| `storage/sqlite.py` | ~4 | 2h |
| `helper_startup.py` | ~5 | 3h |
| `network/knownnodes.py` | ~4 | 2h |

#### Priority 3: Low-Impact Files (remaining ~77)

| Count Range | Files | Effort |
|-------------|-------|--------|
| 1-2 each | ~40 files | 15h total |
| 3-5 each | ~10 files | 10h total |

**Total Effort:** ~63 hours (2-3 weeks)

---

## Phase 3: F-string Conversion (Weeks 3-5)

### Goal: Replace 96 `.format()` calls with f-strings

#### Priority 1: Highest Impact

| File | Count | Risk | Effort |
|------|-------|------|--------|
| `bitmessageqt/mainwindow.py` | 37 | High | 8h |
| `bitmessagekivy/tests/*.py` | 18 | Medium | 4h |

#### Priority 2: Medium Impact

| File | Count | Effort |
|------|-------|--------|
| `bitmessagecli.py` | ~6 | 2h |
| `helper_startup.py` | ~5 | 2h |
| `network/*.py` | ~8 | 3h |

#### Priority 3: Low Impact (remaining ~22)

| Count | Files | Effort |
|-------|-------|--------|
| 1-3 each | ~15 files | 4h |

**Total Effort:** ~23 hours (1-2 weeks)

---

## Phase 4: Type Hints Systematic Adoption (Weeks 5-8)

### Goal: Full type coverage across all modules

#### Module Priority

| Priority | Modules | Coverage | Effort |
|----------|---------|----------|--------|
| P0 | `network/*.py` | 40% | 16h |
| P0 | `storage/*.py` | 60% | 8h |
| P1 | `addresses.py` | 50% | 4h |
| P1 | `helper_*.py` | 30% | 12h |
| P2 | `bitmessageqt/*.py` | 20% | 24h |
| P2 | `bitmessagekivy/*.py` | 15% | 20h |

**Total Effort:** ~84 hours (4 weeks)

---

## Phase 5: Known Issues (FIXMEs)

### Goal: Address critical FIXME comments

| File | Issue | Priority | Effort |
|------|-------|----------|--------|
| `addresses.py` | encodeBase58 should take binary data | High | 4h |
| `networkstatus.py` | Hardcoded stream number | Medium | 2h |
| `class_singleWorker.py` | Inventory deletion, signing | High | 8h |
| `api.py` | XML vulnerabilities, cookie handling | Critical | 16h |

**Total Effort:** ~30 hours

---

## Summary Timeline

```
Week 1:  Phase 1 (type: ignore)          [10h]
Week 2:  Phase 2 (pathlib P1)            [31h]
Week 3:  Phase 2 (pathlib P2) + Phase 3  [31h + 12h]
Week 4:  Phase 3 (complete) + Phase 4    [11h + 21h]
Week 5:  Phase 4 (P0 modules)            [24h]
Week 6:  Phase 4 (P1 modules)            [16h]
Week 7:  Phase 4 (P2 modules)            [24h]
Week 8:  Phase 4 (finish) + Phase 5      [24h + 15h]
```

**Total Estimated Effort:** ~229 hours (8 weeks full-time)

---

## Success Criteria

- [ ] 0 `type: ignore` violations
- [ ] 0 `os.path` usages (replaced with pathlib)
- [ ] 0 `.format()` calls (replaced with f-strings)
- [ ] 80%+ type hint coverage across core modules
- [ ] All FIXME issues addressed or triaged
- [ ] All tests pass after each phase

---

## Dependencies & Blockers

### Blockers
1. **Phase 2**: Need `paths.py` Pathlib migration before `filesystem.py`
2. **Phase 3**: Can run parallel with Phase 2
3. **Phase 4**: Blocked until Phase 1 complete (type stubs needed)
4. **Phase 5**: Can run in parallel with Phases 2-4

### Prerequisites
- Python 3.13+ (✅ already set)
- mypy configured (✅ setup.cfg exists)
- Test coverage baseline (✅ 128 tests passing)

---

## Rollback Strategy

1. **Before each phase**: Create git tag `pre-modernization-[phase]`
2. **After each phase**: Run full test suite, must pass 100%
3. **If failure**: `git checkout pre-modernization-[phase]`
4. **Hotfix window**: 24 hours after each phase completion

---

## Notes

- All changes should be atomic (one file per commit)
- Include type: ignore reason in comment when temporarily needed
- Run `mypy src/` after each file change
- Update AGENTS.md with progress after each phase
