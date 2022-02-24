# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo import models, fields, api, tools
import re


class NiborRate(models.Model):
    _name = 'nibor.rate'
    _description = 'Nibor Rate'

    name = fields.Date(string='Date', required=True, index=True,
                       default=fields.Date.context_today)
    rate = fields.Float(digits=(12, 6), default=1.0, help='The rate of the currency to the currency of rate 1')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('unique_name_per_day', 'unique (name,company_id)', 'Only one Nibor rate per day allowed!'),
        ('currency_rate_check', 'CHECK (rate>0)', 'The Nibor rate must be strictly positive.'),
    ]


class InterestRate(models.Model):
    _name = 'interest.rate'
    _description = 'Interest Rate'

    name = fields.Char()
    add_rate = fields.Float(digits=(12, 6), default=1.0, string='Additional Rate')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    interest_rate = fields.Many2one(
        comodel_name='interest.rate',
        string='Interest rate',
        required=False)


class InterestCalculations(models.Model):
    _name = 'interest.calculation'
    _description = 'Interest Calculations'

    name = fields.Date(string='Date', required=True, index=True,
                       default=fields.Date.context_today)
    nibor_rate = fields.Float(compute='_get_latest_rate')
    interest_rate = fields.Float(compute='_get_rate')
    interest = fields.Float(compute='compute_interest')
    outstanding = fields.Float(
        string='Outstanding',
        required=False)
    cumulative_interest = fields.Float(compute='cumulative_interest')
    previous_balance = fields.Float(string='previous balance', compute='_previous_record', store=True)
    disco = fields.Many2one(
        comodel_name='res.partner',
        string='Disco',
        required=False)
    add_rate = fields.Float(digits=(12, 6), default=1.0, string='Additional Rate')

    @api.multi
    def create_interest(self):
        disco = request.env['res.partner'].search([('customer', '=', True),])
        disco_outstanding = []
        interest_env = self.env['interest.calculation']
        for rec in disco:
            vals = {
                'disco': rec.id,
                'outstanding': rec.credit,
                'add_rate': rec.interest_rate.add_rate,

            }
            disco_outstanding.append(vals)
            interest_env.create(disco_outstanding)

    @api.one
    @api.depends('disco', )
    def _previous_record(self):
        for record in self:
            balance_ids = self.env['interest.calculation'].search([('disco', '=', self.disco.id), ('id', '<', record.id)],
                                                         order='id desc', limit=1)
            previous_record = balance_ids[0]['cumulative_interest'] if balance_ids else 0
            self.previous_balance = previous_record

    @api.one
    @api.depends('previous_balance')
    def cumulative_interest(self):
        self.cumulative_interest = self.previous_balance + self.interest

# class interest_calc(models.Model):
#     _name = 'interest_calc.interest_calc'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100