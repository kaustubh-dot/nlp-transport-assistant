# Phase 24: Unresolved Data Gaps Report

**Date:** 2026-09-18  
**Project:** Chennai Multimodal Public Transport & Places Knowledge Base  
**Status:** Audit Complete  

---

## 1. Overview

This report documents all unresolved factual gaps, deferred items, and pending human decisions across the expanded multimodal transport and geographic datasets. Each item is classified by importance, reason for absence, and whether it can be manually fetched, manually created, or safely postponed.

---

## 2. Unresolved Gaps Register

### Gap 1: Official CUMTA Static GTFS Feed
- **Data Category:** GTFS Integrated Multi-Agency Public Transit Schedule
- **Affected Entities:** Unified network routing (MTC, CMRL, Southern Railway)
- **Importance:** Medium (Overlapping community GTFS + official CMRL API + OSM provides complete structural coverage)
- **Sources Checked:** `cumta.tn.gov.in`, `data.gov.in`, `tn.data.gov.in`
- **Reason Missing:** CUMTA has not published an unauthenticated, publicly downloadable static GTFS zip file on its open portal.
- **Can User Manually Fetch?** Yes, if the user has an institutional login or official contact at CUMTA (`MANUAL_ACTION_REQUIRED.md`, Item 1).
- **Manual Creation Required?** No.
- **Safe to Postpone?** **Yes.** The knowledge base operates reliably on the community GTFS feed and direct operator disclosures.

---

### Gap 2: High-Resolution Station Interior Walking Paths & Skywalk Geometries
- **Data Category:** Pedestrian Infrastructure & Walking Transfers
- **Affected Entities:** Multimodal interchanges (e.g. Central Metro to Central MMC, Guindy Metro to Guindy Suburban, Tambaram)
- **Importance:** High for sub-station walking directions; Low for entity lookup
- **Sources Checked:** GTFS `transfers.txt`, OSM highway=pedestrian
- **Reason Missing:** Fine-grained internal concourse layouts and underground concourse tunnels are rarely surveyed as public OSM ways.
- **Can User Manually Fetch?** No.
- **Manual Creation Required?** Yes, via human verification of walking transfers (`MANUAL_DATASET_REQUIRED.md`, Section 3).
- **Safe to Postpone?** **Yes.** Straight-line candidate transfers with obstacle warnings are preserved in `walking_candidates.csv`.

---

### Gap 3: Official Suburban Train-by-Train Static Schedule Database
- **Data Category:** Timetables & Trip Calendars
- **Affected Entities:** Southern Railway Chennai Suburban lines (Beach–Chengalpattu, Central–Arakkonam, Central–Gummidipoondi)
- **Importance:** Medium for real-time timetable lookup; Low for entity recognition and route routing
- **Sources Checked:** `sr.indianrailways.gov.in`, Indian Railways NTES
- **Reason Missing:** Timetables are published as seasonal PDF booklets or dynamic web forms, not machine-readable GTFS.
- **Can User Manually Fetch?** Yes, official Suburban Pocket Timetable PDF can be placed in `data/raw/southern_railway/2026-09-18/`.
- **Manual Creation Required?** No.
- **Safe to Postpone?** **Yes.** The core NLU assistant MVP explicitly defers minute-level train schedules and responds with recorded operating spans.

---

### Gap 4: MTC Real-Time Bus Vehicle Positions (GTFS-RT)
- **Data Category:** Real-Time Live Vehicle Positions
- **Affected Entities:** Active MTC bus fleet
- **Importance:** Low for static transport knowledge base; High for live vehicle tracking
- **Sources Checked:** `mtcbus.tn.gov.in`, Chennai Bus Mobile App
- **Reason Missing:** Real-time stream requires active mobile app session tokens and live telemetry APIs.
- **Can User Manually Fetch?** No. Requires official enterprise MTC/Chalo API integration.
- **Manual Creation Required?** No.
- **Safe to Postpone?** **Yes.** Live status is explicitly out of scope for the text NLU MVP.

---

### Gap 5: Human-Approved Multimodal Hub Grouping & Landmark Whitelist
- **Data Category:** Domain Curation & Whitelist
- **Affected Entities:** 62 candidate hubs, 211 candidate interchanges, 1,621 candidate landmarks
- **Importance:** High for production canonical sign-off
- **Sources Checked:** Synthesized candidates in `data/manual/`
- **Reason Missing:** In accordance with Hard Stop Protocol Type C, automated code must not fabricate human subjective approval.
- **Can User Manually Fetch?** No.
- **Manual Creation Required?** Yes, review of candidate files in `data/manual/` as outlined in `MANUAL_DATASET_REQUIRED.md`.
- **Safe to Postpone?** **Yes.** Canonical database has populated unverified candidates with `verified = 0`, preserving safety.
