# Load testing

`locustfile.py` targets the NFR/capacity numbers in
`docs/00-product/02-srs.md` §4 and `docs/06-devops-security-qa/
02-security-test-qa.md` "Load Testing":

- NFR-PERF-001: P95 < 300ms for catalog APIs under target load.
- Baseline: 5K RPS search peak, 1K checkout/minute burst.

Two weighted user profiles:

- `CatalogBrowsingUser` (weight 9) — anonymous course/category/tag/search
  browsing, approximating the "5K RPS search peak" traffic.
- `CheckoutUser` (weight 1) — registers a real account, then drives
  create-order → apply-coupon → pay against a pre-seeded course/coupon.
  Pay is exercised against a fully-discounted (100%-off) order
  specifically so it never calls a real payment provider — see
  `apps.commerce.views.PayOrderView`: a `<= 0` total settles immediately
  without a provider adapter call. This tests our own checkout code path,
  not Stripe/PayPal/etc.

A `quitting` event handler checks the aggregate P95 for the catalog
endpoints against NFR-PERF-001 (300ms) and exits non-zero if it's
exceeded — a real, automated gate, not just a number in a report.

## What has actually been verified here

A local smoke run only proves the script itself works end-to-end against
a dev server — **it is not a measurement of whether the platform meets
its documented NFRs.** Meeting the 5K RPS / 1K-checkout-per-minute /
P95-under-300ms targets requires running this at the documented scale
(a distributed Locust swarm, or Locust Cloud, generating from multiple
source IPs) against an environment provisioned like production — real
database size, real network topology, an autoscaled app tier. None of
that exists in this sandbox. Do not read a passing local run as "the
platform meets its NFRs."

What **was** run and confirmed working, locally, against `manage.py
runserver`:

```
SKILLCHAIN_LOADTEST_COURSE_ID=<seeded course id> \
SKILLCHAIN_LOADTEST_COUPON_CODE=<seeded coupon code> \
locust -f loadtests/locustfile.py --headless --host http://localhost:8000 \
  --users 10 --spawn-rate 5 --run-time 20s --print-stats
```

- The full checkout path (register → login → create order → apply a
  100%-off coupon → pay) completed successfully end to end, 0 failures.
- Catalog browsing worked, and its own rate limiting (see M11b:
  `AnonRateThrottle` at 60/min) correctly kicked in and returned 429s
  under even this tiny 10-user local burst — expected, not a bug. This is
  worth planning around for a real run: **at real scale, 5K RPS from a
  small number of load-generator IPs will be throttled by our own
  `AnonRateThrottle`/`ScopedRateThrottle` long before hitting 5K RPS.** A
  real load test needs either distributed source IPs matching real user
  traffic patterns, or a documented, temporary throttle override in the
  target (non-production) environment — not a change made silently here.
- The P95 gate itself fired correctly (`NFR-PERF-001 FAILED: catalog P95
  ...ms > 300ms target`, nonzero exit) — proving the gate works. Failing
  it on a single unscaled local dev process is expected and says nothing
  about the real target.
- This smoke run also caught and fixed a real, pre-existing routing
  issue unrelated to the load test itself: a stale `runserver` process
  left over from earlier in this session was serving an outdated
  URLconf missing `GET /ai/search/` entirely (404 on every request).
  Restarting the dev server resolved it; not a load-test bug.

## Seeding a course + coupon for a local run

`CheckoutUser` needs a real published course and a 100%-off coupon on it
to exist already — it does not create them. A minimal seed, run once
against whichever database the target server points at:

```python
# python manage.py shell
from django.contrib.auth import get_user_model
from apps.catalog.models import Course
from apps.commerce.models import Coupon

User = get_user_model()
instructor, _ = User.objects.get_or_create(email="loadtest-instructor@example.com")
instructor.set_password("x")
instructor.save()

course, _ = Course.objects.get_or_create(
    owner=instructor,
    title="Loadtest Smoke Course",
    defaults={"summary": "seeded for locust", "price_amount": "19.99"},
)
course.status = Course.STATUS_PUBLISHED
course.save(update_fields=["status"])

coupon, _ = Coupon.objects.get_or_create(
    code="LOADTEST100",
    defaults={"discount_type": "percentage", "discount_value": 100, "course": course,
              "created_by": instructor},
)
print(course.id, coupon.code)
```

`get_or_create` throughout — safe to run more than once.

## Running against a real environment

```
SKILLCHAIN_LOADTEST_COURSE_ID=... SKILLCHAIN_LOADTEST_COUPON_CODE=... \
locust -f loadtests/locustfile.py --host https://staging.skillchain.example.com
```

Open the web UI (default `http://localhost:8089`) to drive users/spawn
rate up toward the 5K RPS / 1K-checkout/minute targets, or run headless
with `--users`/`--spawn-rate`/`--run-time` flags. For the real 5K RPS
target, run distributed (`--master` / `--worker` across multiple
machines) — a single Locust process cannot generate that on its own.
