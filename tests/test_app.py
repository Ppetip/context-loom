# SPDX-License-Identifier: GPL-3.0-only
import copy
import itertools
import random
import unittest
from app import pack


def chunk(name, cost, value, source=None, required=False):
    return {"id": name, "source": source or name, "text": "Synthetic " + name, "units": cost, "value": value, "required": required}


class PackingTests(unittest.TestCase):
    def test_beats_first_fit_and_protects_required_source(self):
        data = {"budget": 6, "chunks": [chunk("required",1,0,"p",True), chunk("forbidden-variant",1,100,"p"), chunk("large",5,4), chunk("small",2,3), chunk("other",3,5)]}
        report = pack(data)
        self.assertEqual(report["optimized"]["total_value"], 8)
        self.assertEqual(report["first_fit"]["total_value"], 4)
        self.assertEqual([r["id"] for r in report["optimized"]["selected"]], ["other", "required", "small"])

    def test_matches_independent_exhaustive_search(self):
        rng = random.Random(19)
        for _ in range(80):
            rows = [chunk(str(i),rng.randint(1,5),rng.randint(0,9),str(i//2),i == 0) for i in range(6)]
            budget = rng.randint(rows[0]["units"], 12)
            feasible = []
            for mask in itertools.product((False,True), repeat=6):
                chosen = [r for r, keep in zip(rows,mask) if keep]
                if not mask[0] or len({r["source"] for r in chosen}) != len(chosen): continue
                cost = sum(r["units"] for r in chosen)
                if cost <= budget: feasible.append((sum(r["value"] for r in chosen),cost))
            expected = min(feasible,key=lambda pair:(-pair[0],pair[1]))
            result = pack({"budget":budget,"chunks":rows})
            self.assertEqual((result["optimized"]["total_value"],result["optimized"]["used_units"]),expected)
            self.assertGreaterEqual(result["optimized"]["total_value"],result["first_fit"]["total_value"])

    def test_optimal_selection_is_order_independent_and_preserves_input(self):
        data = {"budget":2,"chunks":[chunk("z",2,5),chunk("a",2,5)]}
        before = copy.deepcopy(data)
        one = pack(data)["optimized"]
        two = pack({**data,"chunks":list(reversed(data["chunks"]))})["optimized"]
        self.assertEqual(one,two); self.assertEqual(data,before)
        self.assertEqual(one["selected"][0]["id"],"a")
        self.assertEqual(len(one["selected"][0]["sha256"]),64)

    def test_required_overflow_and_conflicting_variants_fail(self):
        for data in ({"budget":0,"chunks":[chunk("a",1,2,required=True)]},
                     {"budget":5,"chunks":[chunk("a",1,2,"s",True),chunk("b",1,2,"s",True)]}):
            with self.assertRaises(ValueError): pack(data)

    def test_invalid_late_rows_and_boolean_costs_fail(self):
        for bad in (chunk("b",True,1),chunk("b",0,1),chunk("a",1,2),{"id":"x"}):
            with self.assertRaises(ValueError): pack({"budget":4,"chunks":[chunk("a",1,1),bad]})
        with self.assertRaises(ValueError): pack({"budget":True,"chunks":[]})

    def test_empty_zero_budget_and_no_free_value_assumption(self):
        report = pack({"budget":0,"chunks":[]})
        self.assertEqual(report["optimized"]["selected"],[])
        report = pack({"budget":3,"chunks":[chunk("a",2,0)]})
        self.assertEqual(report["optimized"]["used_units"],0)
