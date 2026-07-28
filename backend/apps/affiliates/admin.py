from django.contrib import admin

from .models import AffiliateAccount, AffiliateCommission, AffiliateReferral


@admin.register(AffiliateAccount)
class AffiliateAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "referral_code", "commission_rate"]
    search_fields = ["user__email", "referral_code"]


@admin.register(AffiliateReferral)
class AffiliateReferralAdmin(admin.ModelAdmin):
    list_display = ["affiliate", "referred_user", "order", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["affiliate__user__email", "referred_user__email"]


@admin.register(AffiliateCommission)
class AffiliateCommissionAdmin(admin.ModelAdmin):
    list_display = ["referral", "commission_amount", "payout_status", "created_at"]
    list_filter = ["payout_status"]
