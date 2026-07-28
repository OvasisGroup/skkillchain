"""
Locust load test targeting the NFR/capacity numbers documented in
docs/00-product/02-srs.md §4 and docs/06-devops-security-qa/
02-security-test-qa.md "Load Testing":

  - NFR-PERF-001: P95 < 300ms for catalog APIs under target load.
  - Baseline: 5K RPS search peak, 1K checkout/minute burst.

Two user profiles, weighted to approximate real traffic mix:

  - CatalogBrowsingUser (weight 9): anonymous course/category/tag/search
    browsing — the "5K RPS search peak" traffic.
  - CheckoutUser (weight 1): registers a real account, then exercises the
    checkout path (create order -> apply a 100%-off coupon -> pay) against
    a pre-seeded course/coupon — the "1K checkout/minute burst" traffic.
    Pay is exercised against a fully-discounted order specifically so this
    never calls out to a real payment provider (see
    apps.commerce.views.PayOrderView: a <= 0 total settles immediately,
    no provider adapter invoked) — this script tests our own code path,
    not a third party's.

Requires an existing published course and an existing 100%-off coupon on
that course (see README.md in this directory for the seed script) —
SKILLCHAIN_LOADTEST_COURSE_ID and SKILLCHAIN_LOADTEST_COUPON_CODE env
vars. CheckoutUser's tasks no-op (with a warning) if either is unset,
so running this against an unseeded environment doesn't just 404-spam.

IMPORTANT — what this script does and doesn't prove: a local run (see
README.md) only proves the script itself works end-to-end against a dev
server. Meeting NFR-PERF-001 and the RPS/burst targets above requires
running this at scale (a Locust distributed swarm, or locust-cloud)
against an environment provisioned like production (real DB size, real
network topology, autoscaled app tier) — infrastructure this sandbox
does not have. Do not read a local pass as "the platform meets its NFRs."
"""

import os
import random
import uuid

from locust import HttpUser, between, events, task

CATALOG_LATENCY_MS_P95_TARGET = 300  # NFR-PERF-001

COURSE_ID = os.environ.get("SKILLCHAIN_LOADTEST_COURSE_ID", "")
COUPON_CODE = os.environ.get("SKILLCHAIN_LOADTEST_COUPON_CODE", "")


class CatalogBrowsingUser(HttpUser):
    """Anonymous catalog/search traffic — no auth required for any of these."""

    weight = 9
    wait_time = between(0.5, 2.5)

    @task(5)
    def list_courses(self):
        self.client.get("/api/v1/courses/", name="/courses/ [list]")

    @task(2)
    def view_course_detail(self):
        if COURSE_ID:
            self.client.get(f"/api/v1/courses/{COURSE_ID}/", name="/courses/{id}/")

    @task(2)
    def list_categories_and_tags(self):
        self.client.get("/api/v1/categories/", name="/categories/")
        self.client.get("/api/v1/tags/", name="/tags/")

    @task(1)
    def semantic_search(self):
        query = random.choice(["python", "data science", "web development", "design"])
        self.client.get("/api/v1/ai/search/", params={"q": query}, name="/ai/search/")


class CheckoutUser(HttpUser):
    """Registers a real account, then drives the checkout path end to end."""

    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        self.access_token = None
        email = f"loadtest-{uuid.uuid4()}@example.com"
        password = "loadtest-password-123"
        register_response = self.client.post(
            "/api/v1/auth/register/",
            json={"email": email, "password": password},
            name="/auth/register/",
        )
        if register_response.status_code != 201:
            return
        login_response = self.client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": password},
            name="/auth/login/",
        )
        if login_response.status_code == 200:
            self.access_token = login_response.json().get("access")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

    @task
    def checkout_with_full_discount(self):
        if not (self.access_token and COURSE_ID and COUPON_CODE):
            return

        order_response = self.client.post(
            "/api/v1/checkout/orders/",
            json={"items": [{"item_type": "course", "item_id": COURSE_ID}]},
            headers=self._auth_headers(),
            name="/checkout/orders/ [create]",
        )
        if order_response.status_code != 201:
            return
        order_id = order_response.json()["id"]

        coupon_response = self.client.post(
            f"/api/v1/checkout/orders/{order_id}/apply-coupon/",
            json={"code": COUPON_CODE},
            headers=self._auth_headers(),
            name="/checkout/orders/{id}/apply-coupon/",
        )
        if coupon_response.status_code != 200:
            return

        self.client.post(
            f"/api/v1/checkout/orders/{order_id}/pay/",
            json={"provider": "stripe"},
            headers=self._auth_headers(),
            name="/checkout/orders/{id}/pay/",
        )


@events.quitting.add_listener
def _check_catalog_latency_nfr(environment, **kwargs):
    """
    Fails the run (nonzero exit) if catalog browsing's aggregate P95
    exceeds NFR-PERF-001 (300ms) — a real, automated gate, not just a
    number printed in a report. Only meaningful once this has been run at
    the actual target load (see the module docstring); a quiet local run
    trivially meeting this proves the gate works, not that the NFR holds
    at 5K RPS.
    """
    catalog_names = {"/courses/ [list]", "/categories/", "/tags/", "/ai/search/"}
    stats = environment.stats
    relevant = [s for name, s in stats.entries.items() if name[0] in catalog_names]
    if not relevant:
        return
    worst_p95 = max(s.get_response_time_percentile(0.95) for s in relevant)
    if worst_p95 > CATALOG_LATENCY_MS_P95_TARGET:
        print(
            f"NFR-PERF-001 FAILED: catalog P95 {worst_p95:.0f}ms > "
            f"{CATALOG_LATENCY_MS_P95_TARGET}ms target"
        )
        environment.process_exit_code = 1
