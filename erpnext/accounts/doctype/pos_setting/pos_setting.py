# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import cint

from frappe.model.document import Document

class PosSetting(Document):
	def get_series(self):
		frappe.get_meta("Sales Invoice").get_field("naming_series").options or ""

	def validate(self):
		self.check_for_duplicate()
		self.validate_expense_account()
		self.validate_all_link_fields()
		
	def check_for_duplicate(self):
		res = frappe.db.sql("""select name, user from `tabPOS Setting` 
			where ifnull(user, '') = %s and name != %s and company = %s""", 
			(self.user, self.name, self.company))
		if res:
			if res[0][1]:
				msgprint("POS Setting '%s' already created for user: '%s' and company: '%s'" % 
					(res[0][0], res[0][1], self.company), raise_exception=1)
			else:
				msgprint("Global POS Setting already created - %s for this company: '%s'" % 
					(res[0][0], self.company), raise_exception=1)

	def validate_expense_account(self):
		if cint(frappe.defaults.get_global_default("auto_accounting_for_stock")) \
				and not self.expense_account:
			msgprint(_("Expense Account is mandatory"), raise_exception=1)

	def validate_all_link_fields(self):
		accounts = {"Account": [self.cash_bank_account, self.income_account, 
			self.expense_account], "Cost Center": [self.cost_center], 
			"Warehouse": [self.warehouse]}
		
		for link_dt, dn_list in accounts.items():
			for link_dn in dn_list:
				if link_dn and not frappe.db.exists({"doctype": link_dt, 
						"company": self.company, "name": link_dn}):
					frappe.throw(link_dn +_(" does not belong to ") + self.company)

	def on_update(self):
		self.set_defaults()

	def on_trash(self):
		self.set_defaults(include_current_pos=False)

	def set_defaults(self, include_current_pos=True):
		frappe.defaults.clear_default("is_pos")
		
		if not include_current_pos:
			condition = " where name != '%s'" % self.name.replace("'", "\'")
		else:
			condition = ""

		pos_view_users = frappe.db.sql_list("""select user 
			from `tabPOS Setting` {0}""".format(condition))
		
		for user in pos_view_users:
			if user:
				frappe.defaults.set_user_default("is_pos", 1, user)
			else:
				frappe.defaults.set_global_default("is_pos", 1)