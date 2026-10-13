# Example business cases

Describe your business like these, in your own words and language. `pd-advisor` answers with a plan. Answers below are examples; yours will use your real pipelines and connectors.

---

## 1. Solo consultant

> I'm a freelance marketing consultant. Pipedrive is a mess, I forget to follow up and I never know what I'll earn next month.

```
Case: solo consultant, messy CRM, missed follow-ups, no revenue view.
Pain -> fix:
- Messy CRM: pd-data-hygiene audit once, fix list CSV.
- Missed follow-ups: pd-morning-brief daily, pd-follow-up drafts nudges.
- No revenue view: pd-pipeline-review forecast mode monthly.
Setup (once):
1. pd-setup, industry = agencies
2. Run "audit my CRM", merge duplicates in Pipedrive
Rhythm:
- Daily: "brief me for today"
- After calls: Nova summarizes; then "update the CRM from my last call" (fields + next steps)
- Monthly: "forecast next month"
Output lands: chat, notes in Pipedrive, fix list file
Needs: Pipedrive (live)
Can't do: invoices not in Pipedrive -> track paid status in a deal field
Try now: "Run pd-setup for a solo consultant"
```

## 2. Manufacturing sales team

> We sell industrial valves through 8 sales reps and 30 distributors across Europe. Quotes go out and nobody chases them. Repeat customers reorder late or go to competitors.

```
Case: 8-rep B2B manufacturer, distributor channel, quotes not chased, late reorders.
Pain -> fix:
- Quotes not chased: pd-morning-brief flags quotes past validity, pd-follow-up drafts chasers.
- Late reorders: pd-account-health renewals mode = reorder radar (last order date + cycle).
- Manager view: pd-pipeline-review weekly by rep.
Setup (once):
1. pd-setup, industry = manufacturing-wholesale
2. Add fields: Quote valid until, Last order date, Reorder cycle (days) (manual)
Rhythm:
- Daily: reps "brief me for today"
- Weekly: manager "pipeline review by rep" -> Slack #sales-eu
- Monthly: "reorder radar next 60 days"
Output lands: chat, Slack (opt-in), Outlook drafts
Needs: Pipedrive (live, manager user for team review), Outlook (optional, missing), Slack (optional, live)
Can't do: ERP order history -> import last order date to Pipedrive monthly
Try now: "Run pd-setup for a manufacturing team"
```

## 3. Recruiting agency (Portuguese)

> Somos uma agência de recrutamento em Lisboa com 4 recrutadores. Perdemos vagas porque os clientes não dão feedback e não sabemos que fees vamos faturar.

```
Caso: agência recrutamento, 4 recrutadores, clientes sem feedback, fees imprevisíveis.
Dor -> solução:
- Sem feedback: pd-morning-brief sinaliza shortlists sem resposta 5+ dias, pd-follow-up rascunha lembrete.
- Fees: pd-pipeline-review forecast por vaga (fee % x salário).
- Aprender: pd-win-loss trimestral em vagas perdidas.
Setup (uma vez):
1. pd-setup, industry = recruiting-staffing
2. Criar campos: Salário, Fee %, Exclusiva, Data shortlist (manual)
Ritmo:
- Diário: "briefing de hoje"
- Após intake: Nova resume a chamada; depois "atualiza o CRM a partir da última chamada" (campos + próximos passos)
- Semanal: "previsão de fees"
Output: chat, notas no Pipedrive, rascunhos Gmail
Precisa: Pipedrive (ligado), Gmail (opcional, ligado)
Não faz: dados de candidatos são dados pessoais. Guardar só o necessário e cumprir o RGPD.
Experimenta: "Corre pd-setup para agência de recrutamento"
```

## 4. SaaS with renewals

> B2B SaaS, 5 AEs and 2 CSMs. New business is OK but renewals surprise us and expansion is random.

```
Case: SaaS, 5 AE + 2 CSM, renewal surprises, random expansion.
Pain -> fix:
- Renewal surprises: pd-account-health renewals 90 days out, weekly.
- Random expansion: pd-account-health health mode flags upsell signals in notes.
- Clean handoff: pd-account-health handoff on every won deal.
Setup (once):
1. pd-setup, industry = saas, renewal_field = "Renewal date"
2. Add field Renewal date if missing; consider a Renewals pipeline
Rhythm:
- On deal won: "handoff brief for <deal>"
- Weekly: CSM "renewals next 90 days"
- Monthly: "account health for my accounts"
Output lands: chat, Google Doc (handoff), pinned org notes
Needs: Pipedrive (live), Google Drive (optional, missing)
Can't do: product usage not in Pipedrive -> add usage field or connect analytics
Try now: "Run pd-setup for SaaS with renewals"
```
