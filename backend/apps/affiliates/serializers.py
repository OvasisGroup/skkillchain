from rest_framework import serializers

from .models import AffiliateAccount, AffiliateCommission, AffiliateReferral


class AffiliateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateAccount
        fields = ["id", "referral_code", "commission_rate"]


class AffiliateReferralSerializer(serializers.ModelSerializer):
    referred_user_email = serializers.EmailField(source="referred_user.email", read_only=True)

    class Meta:
        model = AffiliateReferral
        fields = ["id", "referred_user_email", "order", "status", "created_at"]


class AffiliateCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateCommission
        fields = ["id", "referral", "commission_amount", "payout_status", "created_at"]
