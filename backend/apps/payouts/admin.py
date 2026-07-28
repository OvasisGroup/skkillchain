from django.contrib import admin

from .models import Payout, Transaction, Wallet


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fk_name = "wallet"


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["owner_type", "owner_id", "balance_amount", "currency"]
    search_fields = ["owner_id"]
    inlines = [TransactionInline]


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ["instructor", "amount_net", "status", "period_start", "period_end", "paid_at"]
    list_filter = ["status"]
    search_fields = ["instructor__email"]
    readonly_fields = ["id", "created_at"]
