"""
╔══════════════════════════════════════════════════════════════╗
║  KERALA WAR ROOM — Constituency Intelligence Scorer v3      ║
║                                                             ║
║  P1 Improvements:                                          ║
║  • 6 Constituency Archetypes with archetype-specific       ║
║    signal weights and LS dilution factors                  ║
║  • 2024 Lok Sabha data per seat + dilution by archetype    ║
║  • NDA Vote Transfer Logic (non-linear, archetype-aware)   ║
║                                                             ║
║  P2 Improvements:                                          ║
║  • Local Body weight → 25% (from 20%)                     ║
║  • Community composition → 15% (from 5%)                  ║
║  • Exponential anti-incumbency (2 terms = 6.8% not 4%)    ║
║                                                             ║
║  Bonus:                                                    ║
║  • Star Candidate Override (20 high-profile seats)         ║
║                                                             ║
║  Expert Review Fixes (Option A):                           ║
║  • Swing Index — merges LS/LB/AntiInc into one signal     ║
║  • Cadre Resistance — prevents LDF floor collapse          ║
║  • Deterministic swing cap ±5% (expert recommended)       ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ════════════════════════════════════════════════════════════
# 6 CONSTITUENCY ARCHETYPES + SIGNAL WEIGHTS
# Based on strategist framework — each archetype gets
# different weights for each signal source
# ════════════════════════════════════════════════════════════

ARCHETYPE_CONFIG = {

    "MM": {
        "name":       "Malabar Minority Stronghold",
        "geography":  "Malappuram, Kozhikode Muslim belts, Kasaragod",
        "key_driver": "IUML machinery, minority consolidation, Local Body cadre strength",
        # Signal weights (must sum ~100)
        "w_base":     25,   # 2021 Assembly — still relevant floor
        "w_lb":       30,   # Local Body HIGHEST — machinery decides here
        "w_ls":       15,   # LS signal — MOST diluted (national concerns drove UDF 2024)
        "w_comm":     20,   # Community — Muslim% is structural constant
        "w_news":     10,   # News sentiment — least volatile here
        # 2024 LS dilution: 0.30x — strategic national voting inflated UDF
        "ls_dilution":0.30,
        # NDA transfer: NDA votes split anti-LDF minority vote → hurts UDF
        "nda_transfer":"If NDA>12%: minority sees NDA as threat → consolidates toward LDF, hurting UDF. Apply UDF penalty of 0.4% per 1% NDA above 12%",
        "nda_threshold":12,
        "nda_hurts":  "UDF",
    },

    "CR": {
        "name":       "Central Kerala Christian Rubber Belt",
        "geography":  "Kottayam, Pathanamthitta, Idukki, SE Ernakulam",
        "key_driver": "Church stance (NSB/KC factions), rubber/cardamom prices, UDF traditional base",
        "w_base":     25,
        "w_lb":       20,
        "w_ls":       20,   # Moderate — Christian voters fairly consistent 2024→2026
        "w_comm":     20,   # High — Christian% is decisive
        "w_news":     15,   # Buffer zone, rubber price news matters
        "ls_dilution":0.60, # Moderate dilution — Christian voters more consistent
        "nda_transfer":"If NDA>8%: Christian community NDA protest vote → hurts LDF. Apply LDF penalty 0.3% per 1% NDA above 8%",
        "nda_threshold":8,
        "nda_hurts":  "LDF",
    },

    "CF": {
        "name":       "Coastal Fisher-Folk Belt",
        "geography":  "Alappuzha coast, TVM coast (Varkala-Kovalam), Ernakulam coast",
        "key_driver": "Vizhinjam port, kerosene subsidy, Latin Catholic Church directives, sea erosion",
        "w_base":     25,
        "w_lb":       15,   # Lower — coastal voters volatile, LB less predictive
        "w_ls":       20,
        "w_comm":     15,
        "w_news":     25,   # HIGHEST — react quickly to immediate grievances
        "ls_dilution":0.50,
        "nda_transfer":"If NDA>10%: Latin Catholic NDA vote hurts LDF (anti-development sentiment). LDF penalty 0.3% per 1% NDA above 10%",
        "nda_threshold":10,
        "nda_hurts":  "LDF",
    },

    "HP": {
        "name":       "Highland Plantation Belt",
        "geography":  "Wayanad, Idukki highlands (Devikulam, Udumbanchola), Palakkad eastern",
        "key_driver": "Plantation labor unions (CITU vs INTUC), SC/ST welfare schemes, estate management",
        "w_base":     40,   # HIGHEST — union loyalty very sticky here
        "w_lb":       25,
        "w_ls":       10,   # VERY LOW — union vote doesn't follow LS pattern
        "w_comm":     15,
        "w_news":     10,
        "ls_dilution":0.20, # MOST diluted — 2024 LS national wave barely touches here
        "nda_transfer":"NDA negligible in highlands (<10%). If crosses: tribal vote split, minimal transfer",
        "nda_threshold":10,
        "nda_hurts":  "BOTH",
    },

    "NH": {
        "name":       "NSS/SNDP Heartland",
        "geography":  "Rural Kollam, inland Alappuzha, Southern Thrissur, Palakkad rural",
        "key_driver": "NSS (Nair) vs SNDP (Ezhava) balance, BJP/BDJS Ezhava appeal, Nair vote direction",
        "w_base":     25,
        "w_lb":       25,
        "w_ls":       20,
        "w_comm":     20,   # HIGH — Nair/Ezhava split is decisive
        "w_news":     10,
        "ls_dilution":0.50,
        "nda_transfer":"CRITICAL: If NDA>18%: Ezhava(SNDP)→NDA hurts LDF (LDF penalty 0.5%/1% above 18%). If NDA>20% AND high Nair%: Nair→NDA hurts UDF (UDF penalty 0.3%/1% above 20%)",
        "nda_threshold":18,
        "nda_hurts":  "LDF_PRIMARY",  # Ezhava shift hurts LDF more
    },

    "UI": {
        "name":       "Urban IT Corridor",
        "geography":  "TVM city/Nemom/Kazhakkoottam, Kochi/Ernakulam, Kozhikode city, Thrissur city",
        "key_driver": "Infrastructure, IT ecosystem, middle-class anti-incumbency, aspiration narrative",
        "w_base":     20,   # Lower — urban voters less cadre-loyal
        "w_lb":       15,   # Lower — urban LB less organizational
        "w_ls":       30,   # HIGHEST — urban voters vote similarly LS vs Assembly
        "w_comm":     10,
        "w_news":     25,   # High — urban aspirational voters follow media
        "ls_dilution":0.55, # Moderate — urban more consistent but some dilution
        "nda_transfer":"If NDA>20%: urban BJP vote from Ezhava/Nair hurts LDF primarily. LDF penalty 0.4%/1% above 20%",
        "nda_threshold":20,
        "nda_hurts":  "LDF",
    },
}


# ════════════════════════════════════════════════════════════
# SEAT METADATA — Archetype + 2024 LS + 2025 LB per seat
# ls24_swing: positive = UDF gain vs LDF in 2024 LS
# lb24_swing: positive = UDF momentum in 2025 LB
# ════════════════════════════════════════════════════════════

SEAT_METADATA = {
  # ── KASARAGOD (Kasaragod LS: UDF won, +8% swing) ──
  "Manjeshwaram":       {"arch":"MM","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+4},
  "Kasaragod":          {"arch":"MM","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+4},
  "Udma":               {"arch":"MM","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+4},
  "Kanhangad":          {"arch":"MM","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+4},
  "Thrikaripur":        {"arch":"MM","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+4},

  # ── KANNUR (Kannur LS: UDF won — MAJOR UPSET — +12%) ──
  "Payyanur":           {"arch":"NH","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+0},
  "Kalliasseri":        {"arch":"NH","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+0},
  "Taliparamba":        {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Irikkur":            {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Azhikode":           {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Kannur":             {"arch":"UI","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Dharmadom":          {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Thalassery":         {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Kuthuparamba":       {"arch":"MM","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+0},
  "Mattanur":           {"arch":"NH","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+0},
  "Peravoor":           {"arch":"NH","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+0},

  # ── WAYANAD (Wayanad LS: UDF/Rahul Gandhi won — +15%) ──
  "Mananthavady":       {"arch":"HP","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Sulthan Bathery":    {"arch":"HP","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Kalpetta":           {"arch":"HP","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},

  # ── KOZHIKODE (Kozhikode LS: UDF +7% | Vatakara LS: UDF +5%) ──
  "Vatakara":           {"arch":"CF","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+4},
  "Kuttiady":           {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+4},
  "Nadapuram":          {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+4},
  "Koyilandy":          {"arch":"CF","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Perambra":           {"arch":"NH","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Balussery":          {"arch":"NH","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Elathur":            {"arch":"MM","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Kozhikode North":    {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Kozhikode South":    {"arch":"UI","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Beypore":            {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Kunnamangalam":      {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Koduvally":          {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},
  "Thiruvambady":       {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+4},

  # ── MALAPPURAM (Malappuram LS +4% | Ponnani LS +5%) ──
  "Kondotty":           {"arch":"MM","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+3},
  "Eranad":             {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Nilambur":           {"arch":"MM","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Wandoor":            {"arch":"MM","ls24_swing":+15.0,"ls24_win":"UDF","lb24":+5},
  "Manjeri":            {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Perinthalmanna":     {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Mankada":            {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Malappuram":         {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Vengara":            {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Vallikkunnu":        {"arch":"MM","ls24_swing":+4.0,"ls24_win":"UDF","lb24":+3},
  "Tirurangadi":        {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},
  "Tanur":              {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},
  "Tirur":              {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},
  "Kottakkal":          {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},
  "Thavanur":           {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},
  "Ponnani":            {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+3},

  # ── PALAKKAD (Palakkad LS: UDF +6% | Alathur LS: LDF won -3%) ──
  "Thrithala":          {"arch":"NH","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Pattambi":           {"arch":"MM","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+2},
  "Shornur":            {"arch":"NH","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Ottapalam":          {"arch":"NH","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Kongad":             {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+2},
  "Mannarkkad":         {"arch":"HP","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Malampuzha":         {"arch":"UI","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Palakkad":           {"arch":"UI","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Tarur":              {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+2},
  "Chittur":            {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+2},
  "Nenmara":            {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+2},
  "Alathur":            {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+2},

  # ── THRISSUR (Thrissur LS: UDF +10% | Alathur LS: LDF -3%) ──
  "Chelakkara":         {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+3},
  "Kunnamkulam":        {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+3},
  "Guruvayur":          {"arch":"NH","ls24_swing":-3.0,"ls24_win":"LDF","lb24":+3},
  "Manalur":            {"arch":"NH","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Wadakkanchery":      {"arch":"NH","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Ollur":              {"arch":"NH","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Thrissur":           {"arch":"UI","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Nattika":            {"arch":"CF","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Kaipamangalam":      {"arch":"NH","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Irinjalakuda":       {"arch":"NH","ls24_swing":+10.0,"ls24_win":"UDF","lb24":+3},
  "Puthukkad":          {"arch":"NH","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+3},
  "Chalakudy":          {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+3},
  "Kodungallur":        {"arch":"CF","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+3},

  # ── ERNAKULAM (Chalakudy LS +8% | Ernakulam LS +14%) ──
  "Perumbavoor":        {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+8},
  "Angamaly":           {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+8},
  "Aluva":              {"arch":"UI","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+8},
  "Kalamassery":        {"arch":"UI","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Paravur":            {"arch":"CF","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Vypin":              {"arch":"CF","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Kochi":              {"arch":"UI","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Thrippunithura":     {"arch":"UI","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Ernakulam":          {"arch":"UI","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Thrikkakara":        {"arch":"UI","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Kunnathunad":        {"arch":"CR","ls24_swing":+14.0,"ls24_win":"UDF","lb24":+8},
  "Piravom":            {"arch":"CR","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+8},
  "Muvattupuzha":       {"arch":"CR","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+8},
  "Kothamangalam":      {"arch":"CR","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+8},

  # ── IDUKKI (Idukki LS: UDF +9%) ──
  "Devikulam":          {"arch":"HP","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+5},
  "Udumbanchola":       {"arch":"HP","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+5},
  "Thodupuzha":         {"arch":"CR","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+5},
  "Idukki":             {"arch":"CR","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+5},
  "Peerumade":          {"arch":"HP","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+5},

  # ── KOTTAYAM (Kottayam LS: UDF +8%) ──
  "Pala":               {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Kaduthuruthy":       {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Vaikom":             {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Ettumanoor":         {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Kottayam":           {"arch":"UI","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Puthuppally":        {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Changanassery":      {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Kanjirappally":      {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},
  "Poonjar":            {"arch":"CR","ls24_swing":+8.0,"ls24_win":"UDF","lb24":+5},

  # ── ALAPPUZHA (Alappuzha LS: UDF +5% | Mavelikkara LS: LDF -2%) ──
  "Aroor":              {"arch":"CF","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+2},
  "Cherthala":          {"arch":"CF","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+2},
  "Alappuzha":          {"arch":"CF","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+2},
  "Ambalappuzha":       {"arch":"CF","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+2},
  "Kuttanad":           {"arch":"CF","ls24_swing":-2.0,"ls24_win":"LDF","lb24":+2},
  "Haripad":            {"arch":"NH","ls24_swing":-2.0,"ls24_win":"LDF","lb24":+2},
  "Kayamkulam":         {"arch":"NH","ls24_swing":-2.0,"ls24_win":"LDF","lb24":+2},
  "Mavelikara":         {"arch":"NH","ls24_swing":-2.0,"ls24_win":"LDF","lb24":+2},
  "Chengannur":         {"arch":"NH","ls24_swing":-2.0,"ls24_win":"LDF","lb24":+2},

  # ── PATHANAMTHITTA (Pathanamthitta LS: UDF +12% — LDF swept 2021 Assembly!) ──
  "Thiruvalla":         {"arch":"CR","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+7},
  "Ranni":              {"arch":"CR","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+7},
  "Aranmula":           {"arch":"CR","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+7},
  "Konni":              {"arch":"CR","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+7},
  "Adoor":              {"arch":"NH","ls24_swing":+12.0,"ls24_win":"UDF","lb24":+7},

  # ── KOLLAM (Kollam LS: UDF +9%) ──
  "Karunagapally":      {"arch":"NH","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+6},
  "Chavara":            {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Kunnathur":          {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Kottarakkara":       {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Pathanapuram":       {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Punalur":            {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Chadayamangalam":    {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Kundara":            {"arch":"NH","ls24_swing":+9.0,"ls24_win":"UDF","lb24":+6},
  "Kollam":             {"arch":"UI","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+6},
  "Eravipuram":         {"arch":"CF","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+6},
  "Chathannoor":        {"arch":"NH","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+6},

  # ── THIRUVANANTHAPURAM (TVM LS: UDF +7% | Attingal LS: UDF +6%) ──
  "Varkala":            {"arch":"CF","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+5},
  "Attingal":           {"arch":"CF","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+5},
  "Chirayinkeezhu":     {"arch":"CF","ls24_swing":+6.0,"ls24_win":"UDF","lb24":+5},
  "Nedumangad":         {"arch":"NH","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Vamanapuram":        {"arch":"NH","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Kazhakkoottam":      {"arch":"UI","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Vattiyoorkavu":      {"arch":"UI","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Thiruvananthapuram": {"arch":"UI","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Nemom":              {"arch":"UI","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Aruvikkara":         {"arch":"NH","ls24_swing":+7.0,"ls24_win":"UDF","lb24":+5},
  "Parassala":          {"arch":"NH","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+5},
  "Kattakkada":         {"arch":"NH","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+5},
  "Kovalam":            {"arch":"CF","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+5},
  "Neyyattinkara":      {"arch":"NH","ls24_swing":+5.0,"ls24_win":"UDF","lb24":+5},
}


# ════════════════════════════════════════════════════════════
# STAR CANDIDATE OVERRIDES
# High-profile candidates with personal vote deviating from party
# Applied AFTER AI scoring as a final adjustment
# ════════════════════════════════════════════════════════════

STAR_CANDIDATES = {
  # MASSIVE personal vote — candidate >> party
  "Peravoor":       {"front":"ldf","boost":5,  "note":"K.K. Shailaja — 76% personal approval, massive personal vote. Can resist wave."},
  "Dharmadom":      {"front":"ldf","boost":6,  "note":"Pinarayi Vijayan — home fortress, 10%+ personal vote. LDF floor much higher here."},
  "Thrissur":       {"front":"nda","boost":4,  "note":"Suresh Gopi — Bollywood celebrity, genuine NDA boost. Urban Hindu consolidation."},
  "Malampuzha":     {"front":"nda","boost":5,  "note":"Rajeev Chandrasekhar (BJP president) — highest-profile NDA seat. National spotlight."},

  # Strong personal vote — candidate matters significantly
  "Guruvayur":      {"front":"udf","boost":4,  "note":"V.D. Satheesan (LOP) — fighting personally, high UDF visibility, prestige seat."},
  "Beypore":        {"front":"ldf","boost":3,  "note":"P.A. Mohammed Riyas — CM son-in-law, strong incumbency, Malabar base."},
  "Vatakara":       {"front":"udf","boost":3,  "note":"K.K. Rema (RMPI rebel) — personal anti-LDF icon, strong individual following."},
  "Kazhakkoottam":  {"front":"nda","boost":3,  "note":"Rajeev Chandrasekhar — IT corridor, urban BJP appeal, well-funded campaign."},
  "Kottarakkara":   {"front":"udf","boost":3,  "note":"Ramesh Chennithala — senior Congress leader, decades of local connect."},
  "Palakkad":       {"front":"udf","boost":3,  "note":"Shafi Parambil — high-profile INC candidate, urban presence, strong campaigner."},
  "Thrikkakara":    {"front":"udf","boost":3,  "note":"Eldhose Kunnappilly — won 2022 by-election, proven UDF performer in this seat."},

  # Moderate personal vote — candidate provides extra edge
  "Nemom":          {"front":"ldf","boost":2,  "note":"V. Sivankutty — strong incumbent, personal connect in constituency."},
  "Aranmula":       {"front":"nda","boost":4,  "note":"Kummanam Rajasekharan — BJP veteran, strong Hindu mobilization effort."},
  "Nilambur":       {"front":"udf","boost":2,  "note":"Aryadan Shoukath — personal minority connect, Congress family legacy."},
  "Eranad":         {"front":"udf","boost":2,  "note":"P.K. Basheer — sitting MLA re-contesting, known performer."},
  "Perinthalmanna": {"front":"udf","boost":2,  "note":"Najeeb Kanthapuram — sitting MLA (won 2021 by 38 votes!), tight incumbency."},
  "Thiruvananthapuram":{"front":"ldf","boost":2,"note":"Three-way fight — Sudheer Karamana has LDF local base vs C.P. John (UDF)."},
  "Pala":           {"front":"udf","boost":2,  "note":"Jose Tom Pulikkunnel — KC stronghold, Church backing, UDF traditional seat."},
  "Kunnamangalam":  {"front":"ldf","boost":2,  "note":"P.T.A. Rahim — sitting MLA with Ind-CPI-M support, strong local base."},
  "Irinjalakuda":   {"front":"nda","boost":3,  "note":"NDA strong local organizational base, BJP pushing hard in Thrissur belt."},
  "Vattiyoorkavu":  {"front":"udf","boost":2,  "note":"V.K. Prasanth — energetic INC campaigner, UDF gaining here."},
}


# ════════════════════════════════════════════════════════════
# VERIFIED 2026 CANDIDATES — Source: kerala26.com + keralist.com
# ════════════════════════════════════════════════════════════

CANDIDATES_2026 = {
    # ── KASARAGOD ──────────────────────────────────────────
    "Manjeshwaram":     {"ldf": "K. R. Jayanandan (CPI-M)",            "udf": "A. K. M. Ashraf (IUML)",              "nda": "K. Surendran (BJP)"},
    "Kasaragod":        {"ldf": "Shanavas Padhoor (Ind-LDF)",           "udf": "Kallatra Mahin Haji (IUML)",          "nda": "M. L. Ashwini (BJP)"},
    "Udma":             {"ldf": "C. H. Kunhambu (CPI-M)",               "udf": "K. Neelakandan (INC)",                "nda": "Manulal Meloth (BJP)"},
    "Kanhangad":        {"ldf": "Govindan Pallikkappil (CPI)",          "udf": "Shyji Ottapalli (KEC)",               "nda": "M. Balraj (BJP)"},
    "Thrikaripur":      {"ldf": "V. P. P. Mustafa (CPI-M)",             "udf": "Sandeep Varier (INC)",                "nda": "Ravi Kulangara (T20)"},
    # ── KANNUR ─────────────────────────────────────────────
    "Payyanur":         {"ldf": "T. I. Madhusoodanan (CPI-M)",          "udf": "V. Kunjikrishnan (Ind-UDF)",          "nda": "A. P. Gangadharan (BJP)"},
    "Kalliasseri":      {"ldf": "M. Vijin (CPI-M)",                     "udf": "Rajeevan Kappachery (INC)",           "nda": "A. V. Anilkumar (BJP)"},
    "Taliparamba":      {"ldf": "P. K. Shyamala (CPI-M)",               "udf": "T. K. Govindan (Ind-UDF)",           "nda": "N. Haridas (BJP)"},
    "Irikkur":          {"ldf": "Mathew Kunnapally (KC-M)",             "udf": "Sajeev Joseph (INC)",                 "nda": "Srinath Padmanabhan (T20)"},
    "Azhikode":         {"ldf": "K. V. Sumesh (CPI-M)",                 "udf": "Kareem Cheleri (IUML)",              "nda": "K. K. Vinod Kumar (BJP)"},
    "Kannur":           {"ldf": "Kadanappalli Ramachandran (Cong-S)",   "udf": "T. O. Mohanan (INC)",                "nda": "C. Raghunath (BJP)"},
    "Dharmadom":        {"ldf": "Pinarayi Vijayan (CPI-M)",             "udf": "Abdul Rasheed (INC)",                 "nda": "K. Ranjith (BJP)"},
    "Thalassery":       {"ldf": "Karayi Rajan (CPI-M)",                 "udf": "K. P. Saju (INC)",                   "nda": "O. Nidheesh (BJP)"},
    "Kuthuparamba":     {"ldf": "P. K. Praveen (RJD)",                  "udf": "Jayanthi Rajan (IUML)",              "nda": "Shijilal (BJP)"},
    "Mattanur":         {"ldf": "V. K. Sanoj (CPI-M)",                  "udf": "Chandran Thillenkeri (INC)",          "nda": "Biju Elakkuzhi (BJP)"},
    "Peravoor":         {"ldf": "K. K. Shailaja (CPI-M)",               "udf": "Sunny Joseph (INC)",                  "nda": "Paily Vathiatt (BDJS)"},
    # ── WAYANAD ────────────────────────────────────────────
    "Mananthavady":     {"ldf": "O. R. Kelu (CPI-M)",                   "udf": "Usha Vijayan (INC)",                  "nda": "P. Shyam Raj (BJP)"},
    "Sulthan Bathery":  {"ldf": "M. S. Viswanathan (CPI-M)",            "udf": "I. C. Balakrishnan (INC)",            "nda": "A. S. Kavitha (BJP)"},
    "Kalpetta":         {"ldf": "P. K. Anil Kumar (RJD)",               "udf": "T. Siddique (INC)",                   "nda": "Prashanth Malavayal (BJP)"},
    # ── KOZHIKODE ──────────────────────────────────────────
    "Vatakara":         {"ldf": "M. K. Bhaskaran (RJD)",                "udf": "K. K. Rema (RMPI)",                   "nda": "K. Dileep (BJP)"},
    "Kuttiady":         {"ldf": "K. P. Kunhammadkutty (CPI-M)",        "udf": "Parakkal Abdulla (IUML)",             "nda": "Ramadas Manaleri (BJP)"},
    "Nadapuram":        {"ldf": "P. Vasantham (CPI)",                   "udf": "K. M. Abhijith (INC)",                "nda": "C. P. Vipin Chandran (BJP)"},
    "Koyilandy":        {"ldf": "K. Dasan (CPI-M)",                     "udf": "K. Praveen Kumar (INC)",              "nda": "C. R. Praphul Krishnan (BJP)"},
    "Perambra":         {"ldf": "T. P. Ramakrishnan (CPI-M)",           "udf": "Fathima Thahiliya (IUML)",            "nda": "M. Mohanan Master (BJP)"},
    "Balussery":        {"ldf": "K. M. Sachin Dev (CPI-M)",             "udf": "V. T. Sooraj (INC)",                  "nda": "C. P. Sateeshan (BJP)"},
    "Elathur":          {"ldf": "A. K. Saseendran (NCP-SP)",            "udf": "Vidya Balakrishnan (INC)",            "nda": "T. Devadas (BJP)"},
    "Kozhikode North":  {"ldf": "Thottathil Ravindran (CPI-M)",        "udf": "K. Jayanth (INC)",                    "nda": "Navya Haridas (BJP)"},
    "Kozhikode South":  {"ldf": "Ahamed Devarkovil (INL)",              "udf": "Faisal Babu (IUML)",                  "nda": "T. Reneesh (BJP)"},
    "Beypore":          {"ldf": "P. A. Mohammed Riyas (CPI-M)",         "udf": "P. V. Anvar (Ind-UDF)",              "nda": "K. P. Prakash Babu (BJP)"},
    "Kunnamangalam":    {"ldf": "P. T. A. Rahim (Ind-LDF)",             "udf": "M. A. Razak Master (IUML)",          "nda": "V. K. Sajeevan (BJP)"},
    "Koduvally":        {"ldf": "Saleem Madavoor (Ind-LDF)",            "udf": "P. K. Firos (IUML)",                  "nda": "Giri Pambanal (BDJS)"},
    "Thiruvambady":     {"ldf": "Linto Joseph (CPI-M)",                 "udf": "C. K. Kasim (IUML)",                  "nda": "Sunny Thomas (T20)"},
    # ── MALAPPURAM ─────────────────────────────────────────
    "Kondotty":         {"ldf": "P. Jiji (CPI-M)",                      "udf": "T. P. Ashrafali (IUML)",              "nda": "P. Subhramanyan (BJP)"},
    "Eranad":           {"ldf": "Shafeer Kizhisery (CPI)",              "udf": "P. K. Basheer (IUML)",                "nda": "N. Sreeprakash (BJP)"},
    "Nilambur":         {"ldf": "U. Sharafali (Ind-LDF)",               "udf": "Aryadan Shoukath (INC)",              "nda": "Gireesh Mekkad (BDJS)"},
    "Wandoor":          {"ldf": "K. K. Damodaran (CPI-M)",              "udf": "A. P. Anil Kumar (INC)",              "nda": "E. P. Kumaradas (Ind-NDA)"},
    "Manjeri":          {"ldf": "M. Mustafa (Ind-LDF)",                 "udf": "M. Rahmathulla (IUML)",               "nda": "Pathmasree M. (BJP)"},
    "Perinthalmanna":   {"ldf": "V. P. Muhammad Haneefa (CPI-M)",      "udf": "Najeeb Kanthapuram (IUML)",           "nda": "K. P. Baburaj (BJP)"},
    "Mankada":          {"ldf": "Kunnath Muhammed (Ind-LDF)",           "udf": "Manjalamkuzhi Ali (IUML)",            "nda": "Lijoy Paul (BJP)"},
    "Malappuram":       {"ldf": "T. Mujeeb (NCP-SP)",                   "udf": "P. K. Kunhalikutty (IUML)",           "nda": "Aswathy Gupthakumar (BJP)"},
    "Vengara":          {"ldf": "M. Sabah Kundukuzhikkal (Ind-LDF)",   "udf": "K. M. Shaji (IUML)",                  "nda": "Jayakrishnan V. N. (BJP)"},
    "Vallikkunnu":      {"ldf": "C. P. Musthafa (Ind-LDF)",             "udf": "T. V. Ibrahim (IUML)",                "nda": "M. Preman Master (BJP)"},
    "Tirurangadi":      {"ldf": "Ajit Koladi (CPI)",                    "udf": "P. M. A. Sameer (IUML)",              "nda": "Riju C. Raghav (BJP)"},
    "Tanur":            {"ldf": "P. Mohammed Sameer (Ind-LDF)",         "udf": "P. K. Navas (IUML)",                  "nda": "Deepa Puzhakkal (BJP)"},
    "Tirur":            {"ldf": "V. Abdurahiman (CPI-M)",               "udf": "Kurukkoli Moideen (IUML)",            "nda": "K. Narayanan Master (BJP)"},
    "Kottakkal":        {"ldf": "Preethi Konchath (CPI-M)",             "udf": "K. K. Abid Hussain Thangal (IUML)", "nda": "Subrahmanian Chunkapally (BDJS)"},
    "Thavanur":         {"ldf": "K. T. Jaleel (Ind-LDF)",               "udf": "V. S. Joy (INC)",                     "nda": "Ravi Thelath (BJP)"},
    "Ponnani":          {"ldf": "M. K. Sakeer (CPI-M)",                 "udf": "K. P. Noushad Ali (INC)",             "nda": "E. Maneesh (BDJS)"},
    # ── PALAKKAD ───────────────────────────────────────────
    "Thrithala":        {"ldf": "M. B. Rajesh (CPI-M)",                 "udf": "V. T. Balram (INC)",                  "nda": "V. Unnikrishnan Master (BJP)"},
    "Pattambi":         {"ldf": "Muhammed Muhsin (CPI)",                "udf": "T. P. Shaji (INC)",                   "nda": "P. Manoj (BJP)"},
    "Shornur":          {"ldf": "P. Mammikutty (CPI-M)",                "udf": "P. Harigovindan Master (INC)",        "nda": "Sanku T. Das (BJP)"},
    "Ottapalam":        {"ldf": "K. Premkumar (CPI-M)",                 "udf": "P. K. Sasi (INC)",                    "nda": "Major Ravi (BJP)"},
    "Kongad":           {"ldf": "K. Shanthakumari (CPI-M)",             "udf": "K. A. Thulasi (INC)",                 "nda": "Renu Suresh (BJP)"},
    "Mannarkkad":       {"ldf": "Mansil Abubacker (CPI)",               "udf": "N. Samsudheen (IUML)",                "nda": "Issac Varghese (BDJS)"},
    "Malampuzha":       {"ldf": "E. Prabhakaran (CPI-M)",               "udf": "A. Suresh (INC)",                     "nda": "C. Krishnakumar (BJP)"},
    "Palakkad":         {"ldf": "N. M. R. Rasakh (Ind-LDF)",            "udf": "Ramesh Pisharody (INC)",              "nda": "Sobha Surendran (BJP)"},
    "Tarur":            {"ldf": "P. P. Sumod (CPI-M)",                  "udf": "K. C. Subramanian (INC)",             "nda": "Suresh Babu (BJP)"},
    "Chittur":          {"ldf": "V. Murugadas (ISJD)",                  "udf": "Sumesh Achuthan (INC)",               "nda": "Pranesh Rajendran (BJP)"},
    "Nenmara":          {"ldf": "K. Preman (CPI-M)",                    "udf": "A. Thankappan (INC)",                 "nda": "A. N. Anurag (BDJS)"},
    "Alathur":          {"ldf": "T. M. Sasi (CPI-M)",                   "udf": "K. N. Febin (INC)",                   "nda": "K. V. Prasanna Kumar (BJP)"},
    # ── THRISSUR ───────────────────────────────────────────
    "Chelakkara":       {"ldf": "U. R. Pradeep (CPI-M)",                "udf": "Sivan Veettikkunnu (Ind-UDF)",        "nda": "K. Balakrishnan (BJP)"},
    "Kunnamkulam":      {"ldf": "A. C. Moideen (CPI-M)",                "udf": "P. T. Ajay Mohan (INC)",              "nda": "Rijil K. R. (BDJS)"},
    "Guruvayur":        {"ldf": "N. K. Akbar (CPI-M)",                  "udf": "C. H. Rasheed (IUML)",                "nda": "B. Gopalakrishnan (BJP)"},
    "Manalur":          {"ldf": "C. Raveendranath (CPI-M)",             "udf": "T. N. Prathapan (INC)",               "nda": "K. K. Aneesh Kumar (BJP)"},
    "Wadakkanchery":    {"ldf": "Xavier Chittilappilly (CPI-M)",        "udf": "Vyshak Narayanaswami (INC)",          "nda": "T. S. Ullas Babu (BJP)"},
    "Ollur":            {"ldf": "K. Rajan (CPI)",                       "udf": "Shaji Kodankandath (INC)",             "nda": "Bijoy Thomas (BJP)"},
    "Thrissur":         {"ldf": "Alankode Leelakrishnan (CPI)",         "udf": "Rajan Pallan (INC)",                  "nda": "Padmaja Venugopal (BJP)"},
    "Nattika":          {"ldf": "Geetha Gopi (CPI)",                    "udf": "Sunil Lalur (INC)",                   "nda": "C. C. Mukundan (BJP)"},
    "Kaipamangalam":    {"ldf": "K. K. Valsaraj (CPI)",                 "udf": "T. M. Nazar (INC)",                   "nda": "Athulya Ghosh (BDJS)"},
    "Irinjalakuda":     {"ldf": "R. Bindu (CPI-M)",                     "udf": "Thomas Unniyadan (KEC)",              "nda": "Santhosh Cherkalam (BJP)"},
    "Puthukkad":        {"ldf": "K. K. Ramachandran (CPI-M)",           "udf": "K. M. Babu Raj (INC)",                "nda": "A. Nagesh (BJP)"},
    "Chalakudy":        {"ldf": "Biju Chirayath (KC-M)",                "udf": "T. J. Saneesh Kumar Joseph (INC)",    "nda": "Charly Paul (T20)"},
    "Kodungallur":      {"ldf": "V. R. Sunil (CPI)",                    "udf": "O. J. Janeesh (INC)",                 "nda": "Varghese George (T20)"},
    # ── ERNAKULAM ──────────────────────────────────────────
    "Perumbavoor":      {"ldf": "Basil Paul (KC-M)",                    "udf": "Manoj Moothedan (INC)",               "nda": "Jibi Pathickal (T20)"},
    "Angamaly":         {"ldf": "Saju Paul (CPI-M)",                    "udf": "Roji M. John (INC)",                  "nda": "Promy Kuriakose (T20)"},
    "Aluva":            {"ldf": "A. M. Ariff (CPI-M)",                  "udf": "Anwar Sadath (INC)",                  "nda": "M. A. Brahmaraj (BJP)"},
    "Kalamassery":      {"ldf": "P. Rajeeve (CPI-M)",                   "udf": "V. E. Abdul Gafoor (IUML)",           "nda": "M. P. Binu (BDJS)"},
    "Paravur":          {"ldf": "E. T. Taison (CPI)",                   "udf": "V. D. Satheesan (INC)",               "nda": "Vathsala Prasanna Kumar (BJP)"},
    "Vypin":            {"ldf": "M. B. Shaini (CPI-M)",                 "udf": "Tony Chammany (INC)",                 "nda": "Anitha Thomas (T20)"},
    "Kochi":            {"ldf": "K. J. Maxi (CPI-M)",                   "udf": "Mohammad Shiyas (INC)",               "nda": "Xavier Joolappan (T20)"},
    "Thrippunithura":   {"ldf": "K. N. Unnikrishnan (CPI-M)",           "udf": "Deepak Joy (INC)",                    "nda": "Anjali Nair (T20)"},
    "Ernakulam":        {"ldf": "Sabu George (ISJD)",                   "udf": "T. J. Vinod (INC)",                   "nda": "P. R. Shivashankaran (BJP)"},
    "Thrikkakara":      {"ldf": "Pushpa Das (CPI-M)",                   "udf": "Uma Thomas (INC)",                    "nda": "Akhil Marar (T20)"},
    "Kunnathunad":      {"ldf": "P. V. Srinijin (CPI-M)",              "udf": "V. P. Sajeendran (INC)",              "nda": "Babu Divakaran (T20)"},
    "Piravom":          {"ldf": "Sabu K. Jacob (KC-M)",                 "udf": "Anoop Jacob (KC-J)",                  "nda": "Jibi Abraham (T20)"},
    "Muvattupuzha":     {"ldf": "N. Arun (CPI)",                        "udf": "Mathew Kuzhalnadan (INC)",            "nda": "Sunny Kadoothazhe (T20)"},
    "Kothamangalam":    {"ldf": "Antony John (CPI-M)",                  "udf": "Shibu Thekkumpuram (KEC)",            "nda": "Aji Narayanan (BDJS)"},
    # ── IDUKKI ─────────────────────────────────────────────
    "Devikulam":        {"ldf": "A. Raja (CPI-M)",                      "udf": "F. Raja (INC)",                       "nda": "S. Rajendran (BJP)"},
    "Udumbanchola":     {"ldf": "K. K. Jayachandran (CPI-M)",          "udf": "Senapathy Venu (INC)",                "nda": "Sangeetha Viswanathan (BDJS)"},
    "Thodupuzha":       {"ldf": "Cyriac Chazhikaadan (KC-M)",           "udf": "Apu John Joseph (KEC)",               "nda": "Roy A. Varikkadu (T20)"},
    "Idukki":           {"ldf": "Roshy Augustine (KC-M)",               "udf": "Roy K. Paulose (INC)",                "nda": "Pratheesh Prabha (BDJS)"},
    "Peerumade":        {"ldf": "K. Salim Kumar (CPI)",                 "udf": "Cyriac Thomas (INC)",                 "nda": "V. Ratheesh (BJP)"},
    # ── KOTTAYAM ───────────────────────────────────────────
    "Pala":             {"ldf": "Jose K. Mani (KC-M)",                  "udf": "Mani C. Kappan (Ind-UDF)",           "nda": "Shone George (BJP)"},
    "Kaduthuruthy":     {"ldf": "Nirmala Jimmy (KC-M)",                 "udf": "Mons Joseph (KEC)",                   "nda": "Suresh Ettikunnel (BDJS)"},
    "Vaikom":           {"ldf": "P. Pradeep (CPI)",                     "udf": "K. Binimon (INC)",                    "nda": "K. Ajith (BJP)"},
    "Ettumanoor":       {"ldf": "V. N. Vasavan (CPI-M)",                "udf": "Nattakom Suresh (INC)",               "nda": "Athira D. Nair (T20)"},
    "Kottayam":         {"ldf": "K. Anilkumar (CPI-M)",                 "udf": "Thiruvanchoor Radhakrishnan (INC)",   "nda": "P. Anilkumar (BDJS)"},
    "Puthuppally":      {"ldf": "K. M. Radhakrishnan (CPI-M)",          "udf": "Chandy Oommen (INC)",                 "nda": "Ravindranath Vakathanam (BJP)"},
    "Changanassery":    {"ldf": "Job Michael (KC-M)",                   "udf": "Vinu Job (KEC)",                      "nda": "B. Radhakrishna Menon (BJP)"},
    "Kanjirappally":    {"ldf": "N. Jayaraj (KC-M)",                    "udf": "Rony K Baby (INC)",                   "nda": "George Kurian (BJP)"},
    "Poonjar":          {"ldf": "Sebastian Kulathunkal (KC-M)",         "udf": "Sebastian M. J. (INC)",               "nda": "P. C. George (BJP)"},
    # ── ALAPPUZHA ──────────────────────────────────────────
    "Aroor":            {"ldf": "Daleema (CPI-M)",                      "udf": "Shanimol Usman (INC)",                "nda": "P. S. Jyothis (BDJS)"},
    "Cherthala":        {"ldf": "P. Prasad (CPI)",                      "udf": "K. R. Rajendra Prasad (INC)",         "nda": "T. P. Anantharaj (BDJS)"},
    "Alappuzha":        {"ldf": "P. P. Chitharanjan (CPI-M)",           "udf": "A. D. Thomas (INC)",                  "nda": "M. J. Job (BJP)"},
    "Ambalappuzha":     {"ldf": "H. Salam (CPI-M)",                     "udf": "G. Sudhakaran (Ind-UDF)",            "nda": "Arun Anirudhan (BJP)"},
    "Kuttanad":         {"ldf": "Thomas K. Thomas (NCP-SP)",            "udf": "Reji Cheriyan (KEC)",                 "nda": "Santhosh Santhy (BDJS)"},
    "Haripad":          {"ldf": "T. T. Jismon (CPI)",                   "udf": "Ramesh Chennithala (INC)",            "nda": "Sandeep Vachaspati (BJP)"},
    "Kayamkulam":       {"ldf": "U. Prathibha (CPI-M)",                 "udf": "M. Liju (INC)",                       "nda": "Thambi Mettuthara (BDJS)"},
    "Mavelikara":       {"ldf": "M. S. Arun Kumar (CPI-M)",             "udf": "Muthara Raj (INC)",                   "nda": "Ajimon (BJP)"},
    "Chengannur":       {"ldf": "Saji Cherian (CPI-M)",                 "udf": "Eby Kuriakose (INC)",                 "nda": "M. V. Gopakumar (BJP)"},
    # ── PATHANAMTHITTA ─────────────────────────────────────
    "Thiruvalla":       {"ldf": "Mathew T. Thomas (ISJD)",              "udf": "Varghese Mammen (KEC)",               "nda": "Anoop Antony (BJP)"},
    "Ranni":            {"ldf": "Pramod Narayanan (KC-M)",              "udf": "Pazhakulam Madhu (INC)",              "nda": "Thomas K. Samuel (T20)"},
    "Aranmula":         {"ldf": "Veena George (CPI-M)",                 "udf": "Abin Varkey (INC)",                   "nda": "Kummanam Rajasekharan (BJP)"},
    "Konni":            {"ldf": "K. U. Jenish Kumar (CPI-M)",           "udf": "Satheesh Kochuparambil (INC)",        "nda": "T. P. Sundareshan (BDJS)"},
    "Adoor":            {"ldf": "Praji Sashidharan (CPI)",              "udf": "Santhakumar (INC)",                   "nda": "Pandalam Prathapan (BJP)"},
    # ── KOLLAM ─────────────────────────────────────────────
    "Karunagapally":    {"ldf": "M. S. Thara (CPI)",                    "udf": "C. R. Mahesh (INC)",                  "nda": "V. S. Jithin Dev (BJP)"},
    "Chavara":          {"ldf": "Sujith Vijayanpillai (Ind-LDF)",      "udf": "Shibu Baby John (RSP)",               "nda": "K. R. Rajesh (BJP)"},
    "Kunnathur":        {"ldf": "Kovoor Kunjumon (RSP-L)",             "udf": "Ullas Kovoor (RSP)",                  "nda": "Raji Prasad (BJP)"},
    "Kottarakkara":     {"ldf": "K. N. Balagopal (CPI-M)",             "udf": "P. Aisha Potty (INC)",                "nda": "R. Reshmi (BJP)"},
    "Pathanapuram":     {"ldf": "K. B. Ganesh Kumar (KC-B)",            "udf": "Jyothikumar Chamakkala (INC)",        "nda": "Anil Kumar S. (T20)"},
    "Punalur":          {"ldf": "C. Ajaya Prasad (CPI)",                "udf": "Noushad Yunus (IUML)",                "nda": "B. Raghunathan Pillai (T20)"},
    "Chadayamangalam":  {"ldf": "J. Chinchu Rani (CPI)",               "udf": "M. M. Nazeer (INC)",                  "nda": "R. S. Arun Raj (BJP)"},
    "Kundara":          {"ldf": "S. L. Sajikumar (CPI-M)",             "udf": "P. C. Vishnunadh (INC)",              "nda": "Robin Radhakrishnan (BJP)"},
    "Kollam":           {"ldf": "S. Jayamohan (CPI-M)",                "udf": "Bindhu Krishna (INC)",                "nda": "N. Prathap Kumar (BJP)"},
    "Eravipuram":       {"ldf": "M. Noushad (CPI-M)",                  "udf": "Vishnu Mohan (RSP)",                  "nda": "Saji D. Anand (BDJS)"},
    "Chathannoor":      {"ldf": "R. Rajendran (CPI)",                   "udf": "Sooraj Ravi (INC)",                   "nda": "B. B. Gopakumar (BJP)"},
    # ── THIRUVANANTHAPURAM ─────────────────────────────────
    "Varkala":          {"ldf": "V. Joy (CPI-M)",                       "udf": "Varkala Kahar (INC)",                 "nda": "S. Smitha (BJP)"},
    "Attingal":         {"ldf": "O. S. Ambika (CPI-M)",                 "udf": "Santhosh Bhadran (RSP)",              "nda": "P. Sudheer (BJP)"},
    "Chirayinkeezhu":   {"ldf": "Manoj Idamana (CPI)",                  "udf": "Ramya Haridas (INC)",                 "nda": "B. S. Anoop (BJP)"},
    "Nedumangad":       {"ldf": "G. R. Anil (CPI)",                     "udf": "Meenankal Kumar (INC)",               "nda": "Yuvaraj Gokul (BJP)"},
    "Vamanapuram":      {"ldf": "D. K. Murali (CPI-M)",                 "udf": "Sudheersha Palode (INC)",             "nda": "Venu Karanavar (BDJS)"},
    "Kazhakkoottam":    {"ldf": "Kadakampally Surendran (CPI-M)",      "udf": "Sarathchandra Prasad (INC)",          "nda": "V. Muraleedharan (BJP)"},
    "Vattiyoorkavu":    {"ldf": "V. K. Prasanth (CPI-M)",               "udf": "K. Muraleedharan (INC)",              "nda": "R. Sreelekha (BJP)"},
    "Thiruvananthapuram":{"ldf": "Sudheer Karamana (Ind-LDF)",         "udf": "C. P. John (CMP)",                    "nda": "Karamana Jayan (BJP)"},
    "Nemom":            {"ldf": "V. Sivankutty (CPI-M)",                "udf": "K. S. Sabarinadhan (INC)",            "nda": "Rajeev Chandrasekhar (BJP)"},
    "Aruvikkara":       {"ldf": "G. Steephen (CPI-M)",                  "udf": "V. S. Sivakumar (INC)",               "nda": "Vivek Gopan (BJP)"},
    "Parassala":        {"ldf": "C. K. Hareendran (CPI-M)",             "udf": "Neyyattinkara Sanal (INC)",           "nda": "Gireesh Neyyar (BJP)"},
    "Kattakkada":       {"ldf": "I. B. Sathish (CPI-M)",               "udf": "M. R. Baiju (INC)",                   "nda": "P. K. Krishnadas (BJP)"},
    "Kovalam":          {"ldf": "Bhagat Rufus (Ind-LDF)",               "udf": "M. Vincent (INC)",                    "nda": "T. N. Suresh (BJP)"},
    "Neyyattinkara":    {"ldf": "K. Ancelan (CPI-M)",                   "udf": "N. Sakthan (INC)",                    "nda": "S. Rajasekharan Nair (BJP)"},
}


# ════════════════════════════════════════════════════════════
# ANTI-INCUMBENCY CALCULATOR (EXPONENTIAL)
# LDF has been in power 2 consecutive terms — fatigue is
# non-linear, not flat
# ════════════════════════════════════════════════════════════

def compute_anti_incumbency(terms: int = 2) -> float:
    """
    Residual anti-incumbency — structural fatigue ONLY.
    LS 2024 and LB 2025 already capture the anti-LDF wave.
    This is ONLY the compound fatigue of 2 consecutive terms.
    Formula: base(2.0) * (1 + 0.20 * terms) = 2.8%
    """
    base = 2.0
    return round(base * (1 + 0.20 * terms), 1)

ANTI_INC_BOOST = compute_anti_incumbency(terms=2)  # = 2.8%


# ════════════════════════════════════════════════════════════
# CADRE RESISTANCE SCORES
# Expert recommendation: CPI-M organizational inertia limits
# how much a wave can flip a seat.
# Score 0.0 (no resistance) to 0.9 (near-impenetrable)
# Effective swing = SWING_INDEX * (1 - CADRE_SCORE)
# ════════════════════════════════════════════════════════════

CADRE_RESISTANCE = {
    # ── Kannur — CPI-M's strongest fortress ────────────────
    "Dharmadom":       0.90,  # Pinarayi's seat — absolute fortress
    "Mattanur":        0.85,  # KK Shailaja held 2021 by 61K
    "Kalliasseri":     0.82,  # M Vijin — strong CPI-M cadre
    "Azhikode":        0.80,  # KV Sumesh — LDF won by 6K
    "Thalassery":      0.78,  # AN Shamseer — LDF won by 37K
    # Irikkur: UDF won 2021 — NOT in cadre resistance
    "Peravoor":        0.72,  # KK Shailaja contesting — personal vote
    "Kuthuparamba":    0.65,  # LDF won by 9.5K
    "Payyanur":        0.88,  # LDF won by 49,780 (62.77%) — absolute fortress
    # ── Alappuzha coast — strong LDF labor base ────────────
    "Aroor":           0.80,  # LDF won by 9.4K
    "Ambalappuzha":    0.78,  # LDF won by 7.4K
    "Cherthala":       0.72,  # LDF won by 7.2K
    "Alappuzha":       0.68,  # LDF won by 5.2K
    "Kuttanad":        0.65,  # LDF won by 5.4K
    "Haripad":         0.62,  # LDF won by 6.2K
    # ── Thrissur LDF pockets ───────────────────────────────
    "Manalur":         0.68,  # LDF won by 7.2K
    "Ollur":           0.65,  # LDF won by 5.2K
    "Nattika":         0.65,  # LDF won by 7.4K
    "Kunnamkulam":     0.65,  # LDF won by 6.4K
    # ── Palakkad LDF pockets ───────────────────────────────
    "Kongad":          0.70,  # LDF won by 7.2K
    "Tarur":           0.70,  # LDF won by 7.4K
    "Chittur":         0.68,  # LDF won by 7.2K
    "Nenmara":         0.68,  # LDF won by 7.6K
    "Alathur":         0.65,  # LDF won by 6.8K
    "Shornur":         0.62,  # LDF won by 5.2K
    # ── Kozhikode LDF pockets ──────────────────────────────
    "Kunnamangalam":   0.72,  # PTA Rahim — LDF won by 10K
    "Thiruvambady":    0.68,  # LDF won by 7.8K
    "Perambra":        0.68,  # TP Ramakrishnan — LDF won by 22K
    "Koyilandy":       0.65,  # LDF won by 8.5K
    # ── Plantation belt ────────────────────────────────────
    "Devikulam":       0.72,  # LDF won by 7.2K — union loyalty
    "Udumbanchola":    0.70,  # LDF won by 7.4K — union loyalty
    # ── Kollam LDF pockets ─────────────────────────────────
    "Kunnathur":       0.68,  # LDF won by 7.2K
    "Punalur":         0.62,  # LDF won by 5.2K
    "Karunagapally":   0.60,  # LDF won by 6.2K
}

# Default cadre resistance for seats not listed (low/no LDF stronghold)
DEFAULT_CADRE_RESISTANCE = 0.25


# ════════════════════════════════════════════════════════════
# DEFAULT DISTRICT SIGNALS (from daily pipeline)
# ════════════════════════════════════════════════════════════

DEFAULT_DISTRICT_SIGNALS = {
    "Thiruvananthapuram": {"anti_inc":7,"inflation":8,"nda_surge":8,"udf_momentum":6},
    "Kollam":             {"anti_inc":6,"inflation":7,"nda_surge":3,"udf_momentum":7},
    "Pathanamthitta":     {"anti_inc":7,"inflation":6,"nda_surge":2,"udf_momentum":8},
    "Alappuzha":          {"anti_inc":6,"inflation":7,"nda_surge":2,"udf_momentum":6},
    "Kottayam":           {"anti_inc":6,"inflation":6,"nda_surge":2,"udf_momentum":7},
    "Idukki":             {"anti_inc":5,"inflation":6,"nda_surge":2,"udf_momentum":7},
    "Ernakulam":          {"anti_inc":5,"inflation":6,"nda_surge":3,"udf_momentum":8},
    "Thrissur":           {"anti_inc":7,"inflation":8,"nda_surge":7,"udf_momentum":6},
    "Palakkad":           {"anti_inc":6,"inflation":7,"nda_surge":5,"udf_momentum":6},
    "Malappuram":         {"anti_inc":4,"inflation":6,"nda_surge":1,"udf_momentum":8},
    "Kozhikode":          {"anti_inc":6,"inflation":7,"nda_surge":2,"udf_momentum":7},
    "Wayanad":            {"anti_inc":5,"inflation":6,"nda_surge":2,"udf_momentum":7},
    "Kannur":             {"anti_inc":5,"inflation":6,"nda_surge":2,"udf_momentum":6},
    "Kasaragod":          {"anti_inc":5,"inflation":6,"nda_surge":4,"udf_momentum":7},
}


# ════════════════════════════════════════════════════════════
# BASE 2021 DATA (140 seats)
# ════════════════════════════════════════════════════════════

BASE_2021 = [
  {"id":1,  "name":"Manjeshwaram",      "dist":"Kasaragod",          "udf21":38,"ldf21":30,"nda21":30,"inc":"UDF","margin":745, "minority":40,"ezhava":10,"nair":8, "christian":8, "sc_st":8},
  {"id":2,  "name":"Kasaragod",         "dist":"Kasaragod",          "udf21":48,"ldf21":36,"nda21":14,"inc":"UDF","margin":12901, "minority":35,"ezhava":10,"nair":10,"christian":10,"sc_st":8},
  {"id":3,  "name":"Udma",              "dist":"Kasaragod",          "udf21":34,"ldf21":48,"nda21":14,"inc":"LDF","margin":13322, "minority":38,"ezhava":8, "nair":8, "christian":8, "sc_st":8},
  {"id":4,  "name":"Kanhangad",         "dist":"Kasaragod",          "udf21":36,"ldf21":51,"nda21":14,"inc":"LDF","margin":27139, "minority":32,"ezhava":12,"nair":10,"christian":10,"sc_st":8},
  {"id":5,  "name":"Thrikaripur",       "dist":"Kasaragod",          "udf21":52,"ldf21":32,"nda21":14,"inc":"LDF","margin":9400, "minority":30,"ezhava":10,"nair":10,"christian":8, "sc_st":8},
  {"id":6,  "name":"Payyanur",          "dist":"Kannur",             "udf21":29,"ldf21":63,"nda21":8,"inc":"LDF","margin":49780, "minority":32,"ezhava":12,"nair":12,"christian":8, "sc_st":8},
  {"id":7,  "name":"Kalliasseri",       "dist":"Kannur",             "udf21":36,"ldf21":61,"nda21":3,"inc":"LDF","margin":44393,"minority":28,"ezhava":10,"nair":14,"christian":6, "sc_st":8},
  {"id":8,  "name":"Taliparamba",       "dist":"Kannur",             "udf21":46,"ldf21":52,"nda21":2,"inc":"LDF","margin":22689, "minority":34,"ezhava":10,"nair":12,"christian":8, "sc_st":8},
  {"id":9,  "name":"Irikkur",           "dist":"Kannur",             "udf21":50,"ldf21":37,"nda21":12,"inc":"UDF","margin":10010, "minority":30,"ezhava":10,"nair":12,"christian":6, "sc_st":8},
  {"id":10, "name":"Azhikode",          "dist":"Kannur",             "udf21":46,"ldf21":46,"nda21":8,"inc":"LDF","margin":6141,"minority":28,"ezhava":8, "nair":14,"christian":6, "sc_st":8},
  {"id":11, "name":"Kannur",            "dist":"Kannur",             "udf21":38,"ldf21":45,"nda21":10,"inc":"LDF","margin":1745, "minority":26,"ezhava":10,"nair":16,"christian":8, "sc_st":8},
  {"id":12, "name":"Dharmadom",         "dist":"Kannur",             "udf21":34,"ldf21":60,"nda21":6,"inc":"LDF","margin":50123,"minority":24,"ezhava":8, "nair":18,"christian":6, "sc_st":8},
  {"id":13, "name":"Thalassery",        "dist":"Kannur",             "udf21":36,"ldf21":63,"nda21":1,"inc":"LDF","margin":36801, "minority":28,"ezhava":10,"nair":14,"christian":8, "sc_st":8},
  {"id":14, "name":"Kuthuparamba",      "dist":"Kannur",             "udf21":38,"ldf21":45,"nda21":15,"inc":"LDF","margin":9541, "minority":32,"ezhava":14,"nair":12,"christian":8, "sc_st":8},
  {"id":15, "name":"Mattanur",          "dist":"Kannur",             "udf21":34,"ldf21":62,"nda21":4, "inc":"LDF","margin":60963,"minority":22,"ezhava":8, "nair":18,"christian":6, "sc_st":8},
  {"id":16, "name":"Peravoor",          "dist":"Kannur",             "udf21":47,"ldf21":44,"nda21":8, "inc":"UDF","margin":3172, "minority":30,"ezhava":12,"nair":14,"christian":8, "sc_st":8},
  {"id":17, "name":"Mananthavady",      "dist":"Wayanad",            "udf21":38,"ldf21":48,"nda21":12,"inc":"LDF","margin":9282, "minority":20,"ezhava":8, "nair":8, "christian":30,"sc_st":20},
  {"id":18, "name":"Sulthan Bathery",   "dist":"Wayanad",            "udf21":49,"ldf21":36,"nda21":12,"inc":"UDF","margin":11822, "minority":18,"ezhava":10,"nair":8, "christian":28,"sc_st":22},
  {"id":19, "name":"Kalpetta",          "dist":"Wayanad",            "udf21":46,"ldf21":34,"nda21":12,"inc":"UDF","margin":5470, "minority":22,"ezhava":8, "nair":8, "christian":26,"sc_st":20},
  {"id":20, "name":"Vatakara",          "dist":"Kozhikode",          "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":7491, "minority":38,"ezhava":10,"nair":12,"christian":8, "sc_st":6},
  {"id":21, "name":"Kuttiady",          "dist":"Kozhikode",          "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":7800, "minority":40,"ezhava":8, "nair":10,"christian":6, "sc_st":6},
  {"id":22, "name":"Nadapuram",         "dist":"Kozhikode",          "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":7200, "minority":42,"ezhava":8, "nair":10,"christian":6, "sc_st":6},
  {"id":23, "name":"Koyilandy",         "dist":"Kozhikode",          "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":30,"ezhava":14,"nair":14,"christian":6, "sc_st":8},
  {"id":24, "name":"Perambra",          "dist":"Kozhikode",          "udf21":38,"ldf21":53,"nda21":9,"inc":"LDF","margin":22592, "minority":28,"ezhava":12,"nair":16,"christian":6, "sc_st":8},
  {"id":25, "name":"Balussery",         "dist":"Kozhikode",          "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":26,"ezhava":14,"nair":16,"christian":6, "sc_st":8},
  {"id":26, "name":"Elathur",           "dist":"Kozhikode",          "udf21":38,"ldf21":51,"nda21":11,"inc":"LDF","margin":38502, "minority":28,"ezhava":10,"nair":16,"christian":6, "sc_st":8},
  {"id":27, "name":"Kozhikode North",   "dist":"Kozhikode",          "udf21":40,"ldf21":46,"nda21":12,"inc":"LDF","margin":4200, "minority":32,"ezhava":12,"nair":16,"christian":8, "sc_st":6},
  {"id":28, "name":"Kozhikode South",   "dist":"Kozhikode",          "udf21":38,"ldf21":46,"nda21":14,"inc":"LDF","margin":12459, "minority":36,"ezhava":10,"nair":14,"christian":10,"sc_st":6},
  {"id":29, "name":"Beypore",           "dist":"Kozhikode",          "udf21":50,"ldf21":37,"nda21":12,"inc":"LDF","margin":28747, "minority":44,"ezhava":12,"nair":12,"christian":6, "sc_st":6},
  {"id":30, "name":"Kunnamangalam",     "dist":"Kozhikode",          "udf21":38,"ldf21":44,"nda21":10,"inc":"LDF","margin":10276, "minority":26,"ezhava":12,"nair":16,"christian":6, "sc_st":8},
  {"id":31, "name":"Koduvally",         "dist":"Kozhikode",          "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":6344, "minority":42,"ezhava":8, "nair":10,"christian":6, "sc_st":6},
  {"id":32, "name":"Thiruvambady",      "dist":"Kozhikode",          "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7800, "minority":30,"ezhava":10,"nair":14,"christian":6, "sc_st":8},
  {"id":33, "name":"Kondotty",          "dist":"Malappuram",         "udf21":56,"ldf21":30,"nda21":12,"inc":"UDF","margin":17666,"minority":60,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":34, "name":"Eranad",            "dist":"Malappuram",         "udf21":55,"ldf21":32,"nda21":12,"inc":"UDF","margin":22546, "minority":56,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":35, "name":"Nilambur",          "dist":"Malappuram",         "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5400, "minority":48,"ezhava":8, "nair":8, "christian":6, "sc_st":6},
  {"id":36, "name":"Wandoor",           "dist":"Malappuram",         "udf21":52,"ldf21":34,"nda21":10,"inc":"UDF","margin":15563, "minority":50,"ezhava":6, "nair":6, "christian":4, "sc_st":6},
  {"id":37, "name":"Manjeri",           "dist":"Malappuram",         "udf21":58,"ldf21":28,"nda21":12,"inc":"UDF","margin":14573,"minority":62,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":38, "name":"Perinthalmanna",    "dist":"Malappuram",         "udf21":54,"ldf21":32,"nda21":12,"inc":"UDF","margin":38,   "minority":58,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":39, "name":"Mankada",           "dist":"Malappuram",         "udf21":50,"ldf21":38,"nda21":10,"inc":"UDF","margin":6246, "minority":46,"ezhava":8, "nair":8, "christian":6, "sc_st":6},
  {"id":40, "name":"Malappuram",        "dist":"Malappuram",         "udf21":58,"ldf21":30,"nda21":12,"inc":"UDF","margin":35208,"minority":60,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":41, "name":"Vengara",           "dist":"Malappuram",         "udf21":58,"ldf21":28,"nda21":12,"inc":"UDF","margin":30596,"minority":62,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":42, "name":"Vallikkunnu",       "dist":"Malappuram",         "udf21":54,"ldf21":32,"nda21":12,"inc":"UDF","margin":14116,"minority":60,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":43, "name":"Tirurangadi",       "dist":"Malappuram",         "udf21":58,"ldf21":28,"nda21":12,"inc":"UDF","margin":16400,"minority":62,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":44, "name":"Tanur",             "dist":"Malappuram",         "udf21":56,"ldf21":30,"nda21":12,"inc":"UDF","margin":14200,"minority":60,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":45, "name":"Tirur",             "dist":"Malappuram",         "udf21":58,"ldf21":30,"nda21":10,"inc":"UDF","margin":15800,"minority":62,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":46, "name":"Kottakkal",         "dist":"Malappuram",         "udf21":54,"ldf21":32,"nda21":12,"inc":"UDF","margin":12200,"minority":58,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":47, "name":"Thavanur",          "dist":"Malappuram",         "udf21":52,"ldf21":34,"nda21":12,"inc":"LDF","margin":2564, "minority":56,"ezhava":6, "nair":6, "christian":4, "sc_st":4},
  {"id":48, "name":"Ponnani",           "dist":"Malappuram",         "udf21":56,"ldf21":30,"nda21":12,"inc":"UDF","margin":14800,"minority":62,"ezhava":4, "nair":4, "christian":4, "sc_st":4},
  {"id":49, "name":"Thrithala",         "dist":"Palakkad",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":20,"ezhava":16,"nair":18,"christian":6, "sc_st":10},
  {"id":50, "name":"Pattambi",          "dist":"Palakkad",           "udf21":52,"ldf21":34,"nda21":12,"inc":"LDF","margin":8400, "minority":36,"ezhava":12,"nair":16,"christian":6, "sc_st":8},
  {"id":51, "name":"Shornur",           "dist":"Palakkad",           "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":24,"ezhava":14,"nair":16,"christian":8, "sc_st":8},
  {"id":52, "name":"Ottapalam",         "dist":"Palakkad",           "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5400, "minority":22,"ezhava":16,"nair":18,"christian":6, "sc_st":8},
  {"id":53, "name":"Kongad",            "dist":"Palakkad",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":16,"ezhava":18,"nair":18,"christian":6, "sc_st":12},
  {"id":54, "name":"Mannarkkad",        "dist":"Palakkad",           "udf21":50,"ldf21":34,"nda21":14,"inc":"LDF","margin":7800, "minority":32,"ezhava":12,"nair":14,"christian":6, "sc_st":8},
  {"id":55, "name":"Malampuzha",        "dist":"Palakkad",           "udf21":32,"ldf21":28,"nda21":38,"inc":"LDF","margin":3200, "minority":8, "ezhava":24,"nair":18,"christian":6, "sc_st":12},
  {"id":56, "name":"Palakkad",          "dist":"Palakkad",           "udf21":38,"ldf21":36,"nda21":24,"inc":"LDF","margin":1800, "minority":30,"ezhava":16,"nair":14,"christian":8, "sc_st":8},
  {"id":57, "name":"Tarur",             "dist":"Palakkad",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":16,"ezhava":18,"nair":18,"christian":6, "sc_st":12},
  {"id":58, "name":"Chittur",           "dist":"Palakkad",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":14,"ezhava":20,"nair":18,"christian":6, "sc_st":12},
  {"id":59, "name":"Nenmara",           "dist":"Palakkad",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7600, "minority":12,"ezhava":22,"nair":18,"christian":6, "sc_st":12},
  {"id":60, "name":"Alathur",           "dist":"Palakkad",           "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6800, "minority":14,"ezhava":20,"nair":18,"christian":6, "sc_st":12},
  {"id":61, "name":"Chelakkara",        "dist":"Thrissur",           "udf21":42,"ldf21":40,"nda21":16,"inc":"LDF","margin":1400, "minority":20,"ezhava":18,"nair":16,"christian":12,"sc_st":10},
  {"id":62, "name":"Kunnamkulam",       "dist":"Thrissur",           "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6400, "minority":18,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":63, "name":"Guruvayur",         "dist":"Thrissur",           "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5600, "minority":16,"ezhava":22,"nair":20,"christian":18,"sc_st":8},
  {"id":64, "name":"Manalur",           "dist":"Thrissur",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":14,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":65, "name":"Wadakkanchery",     "dist":"Thrissur",           "udf21":42,"ldf21":41,"nda21":15,"inc":"LDF","margin":800,  "minority":16,"ezhava":18,"nair":18,"christian":16,"sc_st":10},
  {"id":66, "name":"Ollur",             "dist":"Thrissur",           "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":18,"ezhava":20,"nair":18,"christian":16,"sc_st":10},
  {"id":67, "name":"Thrissur",          "dist":"Thrissur",           "udf21":36,"ldf21":34,"nda21":28,"inc":"LDF","margin":2400, "minority":28,"ezhava":22,"nair":14,"christian":24,"sc_st":6},
  {"id":68, "name":"Nattika",           "dist":"Thrissur",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":16,"ezhava":22,"nair":18,"christian":12,"sc_st":10},
  {"id":69, "name":"Kaipamangalam",     "dist":"Thrissur",           "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6200, "minority":18,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":70, "name":"Irinjalakuda",      "dist":"Thrissur",           "udf21":35,"ldf21":33,"nda21":30,"inc":"LDF","margin":1200, "minority":25,"ezhava":20,"nair":16,"christian":18,"sc_st":8},
  {"id":71, "name":"Puthukkad",         "dist":"Thrissur",           "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6400, "minority":16,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":72, "name":"Chalakudy",         "dist":"Thrissur",           "udf21":44,"ldf21":40,"nda21":14,"inc":"LDF","margin":2800, "minority":20,"ezhava":18,"nair":16,"christian":30,"sc_st":8},
  {"id":73, "name":"Kodungallur",       "dist":"Thrissur",           "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6200, "minority":22,"ezhava":18,"nair":18,"christian":20,"sc_st":10},
  {"id":74, "name":"Perumbavoor",       "dist":"Ernakulam",          "udf21":52,"ldf21":35,"nda21":11,"inc":"UDF","margin":9800, "minority":22,"ezhava":15,"nair":12,"christian":35,"sc_st":6},
  {"id":75, "name":"Angamaly",          "dist":"Ernakulam",          "udf21":54,"ldf21":32,"nda21":12,"inc":"UDF","margin":12400,"minority":18,"ezhava":12,"nair":10,"christian":42,"sc_st":6},
  {"id":76, "name":"Aluva",             "dist":"Ernakulam",          "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":10200,"minority":20,"ezhava":14,"nair":12,"christian":36,"sc_st":6},
  {"id":77, "name":"Kalamassery",       "dist":"Ernakulam",          "udf21":42,"ldf21":46,"nda21":10,"inc":"LDF","margin":2800, "minority":18,"ezhava":16,"nair":14,"christian":28,"sc_st":8},
  {"id":78, "name":"Paravur",           "dist":"Ernakulam",          "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":8200, "minority":20,"ezhava":14,"nair":12,"christian":32,"sc_st":6},
  {"id":79, "name":"Vypin",             "dist":"Ernakulam",          "udf21":52,"ldf21":34,"nda21":12,"inc":"LDF","margin":9600, "minority":18,"ezhava":12,"nair":12,"christian":36,"sc_st":6},
  {"id":80, "name":"Kochi",             "dist":"Ernakulam",          "udf21":50,"ldf21":34,"nda21":14,"inc":"UDF","margin":8800, "minority":22,"ezhava":12,"nair":14,"christian":32,"sc_st":6},
  {"id":81, "name":"Thrippunithura",    "dist":"Ernakulam",          "udf21":48,"ldf21":34,"nda21":16,"inc":"UDF","margin":7200, "minority":16,"ezhava":14,"nair":16,"christian":30,"sc_st":6},
  {"id":82, "name":"Ernakulam",         "dist":"Ernakulam",          "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":10400,"minority":20,"ezhava":12,"nair":14,"christian":30,"sc_st":6},
  {"id":83, "name":"Thrikkakara",       "dist":"Ernakulam",          "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":8200, "minority":18,"ezhava":14,"nair":14,"christian":32,"sc_st":6},
  {"id":84, "name":"Kunnathunad",       "dist":"Ernakulam",          "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":8400, "minority":16,"ezhava":16,"nair":14,"christian":34,"sc_st":6},
  {"id":85, "name":"Piravom",           "dist":"Ernakulam",          "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":9200, "minority":14,"ezhava":12,"nair":12,"christian":40,"sc_st":6},
  {"id":86, "name":"Muvattupuzha",      "dist":"Ernakulam",          "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":9600, "minority":16,"ezhava":12,"nair":12,"christian":38,"sc_st":6},
  {"id":87, "name":"Kothamangalam",     "dist":"Ernakulam",          "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":8200, "minority":14,"ezhava":10,"nair":12,"christian":40,"sc_st":6},
  {"id":88, "name":"Devikulam",         "dist":"Idukki",             "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":10,"ezhava":8, "nair":8, "christian":42,"sc_st":18},
  {"id":89, "name":"Udumbanchola",      "dist":"Idukki",             "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":12,"ezhava":8, "nair":8, "christian":40,"sc_st":18},
  {"id":90, "name":"Thodupuzha",        "dist":"Idukki",             "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":8200, "minority":10,"ezhava":8, "nair":10,"christian":48,"sc_st":12},
  {"id":91, "name":"Idukki",            "dist":"Idukki",             "udf21":48,"ldf21":38,"nda21":12,"inc":"UDF","margin":6400, "minority":12,"ezhava":8, "nair":10,"christian":44,"sc_st":14},
  {"id":92, "name":"Peerumade",         "dist":"Idukki",             "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":9200, "minority":10,"ezhava":6, "nair":8, "christian":50,"sc_st":14},
  {"id":93, "name":"Pala",              "dist":"Kottayam",           "udf21":45,"ldf21":43,"nda21":10,"inc":"LDF","margin":1100, "minority":10,"ezhava":8, "nair":10,"christian":52,"sc_st":8},
  {"id":94, "name":"Kaduthuruthy",      "dist":"Kottayam",           "udf21":52,"ldf21":36,"nda21":10,"inc":"LDF","margin":9400, "minority":8, "ezhava":6, "nair":10,"christian":56,"sc_st":8},
  {"id":95, "name":"Vaikom",            "dist":"Kottayam",           "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":12,"ezhava":20,"nair":18,"christian":32,"sc_st":8},
  {"id":96, "name":"Ettumanoor",        "dist":"Kottayam",           "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":10,"ezhava":16,"nair":16,"christian":38,"sc_st":8},
  {"id":97, "name":"Kottayam",          "dist":"Kottayam",           "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":8200, "minority":10,"ezhava":10,"nair":14,"christian":52,"sc_st":6},
  {"id":98, "name":"Puthuppally",       "dist":"Kottayam",           "udf21":54,"ldf21":32,"nda21":12,"inc":"UDF","margin":12400,"minority":6, "ezhava":6, "nair":8, "christian":62,"sc_st":6},
  {"id":99, "name":"Changanassery",     "dist":"Kottayam",           "udf21":52,"ldf21":34,"nda21":12,"inc":"UDF","margin":10200,"minority":8, "ezhava":8, "nair":10,"christian":58,"sc_st":6},
  {"id":100,"name":"Kanjirappally",     "dist":"Kottayam",           "udf21":50,"ldf21":36,"nda21":12,"inc":"UDF","margin":8200, "minority":8, "ezhava":8, "nair":10,"christian":54,"sc_st":8},
  {"id":101,"name":"Poonjar",           "dist":"Kottayam",           "udf21":48,"ldf21":38,"nda21":12,"inc":"LDF","margin":6400, "minority":8, "ezhava":8, "nair":10,"christian":52,"sc_st":8},
  {"id":102,"name":"Aroor",             "dist":"Alappuzha",          "udf21":38,"ldf21":52,"nda21":8, "inc":"LDF","margin":9400, "minority":14,"ezhava":24,"nair":14,"christian":18,"sc_st":10},
  {"id":103,"name":"Cherthala",         "dist":"Alappuzha",          "udf21":39,"ldf21":50,"nda21":9, "inc":"LDF","margin":7200, "minority":16,"ezhava":22,"nair":14,"christian":20,"sc_st":10},
  {"id":104,"name":"Alappuzha",         "dist":"Alappuzha",          "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":18,"ezhava":24,"nair":14,"christian":16,"sc_st":10},
  {"id":105,"name":"Ambalappuzha",      "dist":"Alappuzha",          "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7400, "minority":16,"ezhava":26,"nair":12,"christian":14,"sc_st":10},
  {"id":106,"name":"Kuttanad",          "dist":"Alappuzha",          "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5400, "minority":14,"ezhava":22,"nair":14,"christian":18,"sc_st":12},
  {"id":107,"name":"Haripad",           "dist":"Alappuzha",          "udf21":40,"ldf21":49,"nda21":9, "inc":"LDF","margin":6200, "minority":16,"ezhava":22,"nair":14,"christian":16,"sc_st":10},
  {"id":108,"name":"Kayamkulam",        "dist":"Alappuzha",          "udf21":48,"ldf21":40,"nda21":10,"inc":"LDF","margin":5200, "minority":20,"ezhava":22,"nair":14,"christian":18,"sc_st":10},
  {"id":109,"name":"Mavelikara",        "dist":"Alappuzha",          "udf21":46,"ldf21":40,"nda21":12,"inc":"LDF","margin":4200, "minority":16,"ezhava":18,"nair":14,"christian":24,"sc_st":10},
  {"id":110,"name":"Chengannur",        "dist":"Alappuzha",          "udf21":48,"ldf21":38,"nda21":12,"inc":"UDF","margin":6200, "minority":12,"ezhava":16,"nair":16,"christian":30,"sc_st":10},
  {"id":111,"name":"Thiruvalla",        "dist":"Pathanamthitta",     "udf21":50,"ldf21":36,"nda21":12,"inc":"LDF","margin":8400, "minority":8, "ezhava":8, "nair":14,"christian":58,"sc_st":6},
  {"id":112,"name":"Ranni",             "dist":"Pathanamthitta",     "udf21":48,"ldf21":38,"nda21":12,"inc":"LDF","margin":6200, "minority":6, "ezhava":8, "nair":14,"christian":56,"sc_st":8},
  {"id":113,"name":"Aranmula",          "dist":"Pathanamthitta",     "udf21":46,"ldf21":38,"nda21":14,"inc":"LDF","margin":5400, "minority":8, "ezhava":10,"nair":14,"christian":48,"sc_st":8},
  {"id":114,"name":"Konni",             "dist":"Pathanamthitta",     "udf21":47,"ldf21":40,"nda21":11,"inc":"LDF","margin":4800, "minority":8, "ezhava":12,"nair":14,"christian":44,"sc_st":10},
  {"id":115,"name":"Adoor",             "dist":"Pathanamthitta",     "udf21":42,"ldf21":46,"nda21":10,"inc":"LDF","margin":2400, "minority":10,"ezhava":14,"nair":16,"christian":38,"sc_st":10},
  {"id":116,"name":"Karunagapally",     "dist":"Kollam",             "udf21":39,"ldf21":49,"nda21":10,"inc":"LDF","margin":6200, "minority":14,"ezhava":24,"nair":18,"christian":12,"sc_st":10},
  {"id":117,"name":"Chavara",           "dist":"Kollam",             "udf21":46,"ldf21":42,"nda21":10,"inc":"LDF","margin":2800, "minority":14,"ezhava":22,"nair":18,"christian":14,"sc_st":10},
  {"id":118,"name":"Kunnathur",         "dist":"Kollam",             "udf21":38,"ldf21":50,"nda21":10,"inc":"LDF","margin":7200, "minority":12,"ezhava":24,"nair":20,"christian":12,"sc_st":10},
  {"id":119,"name":"Kottarakkara",      "dist":"Kollam",             "udf21":49,"ldf21":38,"nda21":11,"inc":"LDF","margin":6800, "minority":12,"ezhava":20,"nair":20,"christian":14,"sc_st":10},
  {"id":120,"name":"Pathanapuram",      "dist":"Kollam",             "udf21":46,"ldf21":40,"nda21":12,"inc":"LDF","margin":3800, "minority":12,"ezhava":22,"nair":18,"christian":12,"sc_st":10},
  {"id":121,"name":"Punalur",           "dist":"Kollam",             "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":12,"ezhava":22,"nair":18,"christian":12,"sc_st":12},
  {"id":122,"name":"Chadayamangalam",   "dist":"Kollam",             "udf21":39,"ldf21":47,"nda21":12,"inc":"LDF","margin":5600, "minority":10,"ezhava":24,"nair":20,"christian":12,"sc_st":10},
  {"id":123,"name":"Kundara",           "dist":"Kollam",             "udf21":44,"ldf21":43,"nda21":11,"inc":"LDF","margin":800,  "minority":12,"ezhava":22,"nair":18,"christian":14,"sc_st":10},
  {"id":124,"name":"Kollam",            "dist":"Kollam",             "udf21":48,"ldf21":40,"nda21":10,"inc":"LDF","margin":5200, "minority":14,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":125,"name":"Eravipuram",        "dist":"Kollam",             "udf21":40,"ldf21":48,"nda21":10,"inc":"LDF","margin":5200, "minority":12,"ezhava":22,"nair":18,"christian":12,"sc_st":10},
  {"id":126,"name":"Chathannoor",       "dist":"Kollam",             "udf21":47,"ldf21":38,"nda21":13,"inc":"LDF","margin":5400, "minority":12,"ezhava":20,"nair":18,"christian":14,"sc_st":10},
  {"id":127,"name":"Varkala",           "dist":"Thiruvananthapuram", "udf21":39,"ldf21":46,"nda21":13,"inc":"LDF","margin":4600, "minority":12,"ezhava":22,"nair":22,"christian":10,"sc_st":12},
  {"id":128,"name":"Attingal",          "dist":"Thiruvananthapuram", "udf21":35,"ldf21":34,"nda21":29,"inc":"LDF","margin":800,  "minority":15,"ezhava":20,"nair":20,"christian":12,"sc_st":12},
  {"id":129,"name":"Chirayinkeezhu",    "dist":"Thiruvananthapuram", "udf21":37,"ldf21":45,"nda21":16,"inc":"LDF","margin":5200, "minority":14,"ezhava":22,"nair":20,"christian":10,"sc_st":12},
  {"id":130,"name":"Nedumangad",        "dist":"Thiruvananthapuram", "udf21":38,"ldf21":46,"nda21":14,"inc":"LDF","margin":5400, "minority":14,"ezhava":20,"nair":22,"christian":12,"sc_st":12},
  {"id":131,"name":"Vamanapuram",       "dist":"Thiruvananthapuram", "udf21":42,"ldf21":41,"nda21":15,"inc":"LDF","margin":600,  "minority":14,"ezhava":22,"nair":20,"christian":10,"sc_st":12},
  {"id":132,"name":"Kazhakkoottam",     "dist":"Thiruvananthapuram", "udf21":33,"ldf21":32,"nda21":33,"inc":"LDF","margin":600,  "minority":18,"ezhava":16,"nair":16,"christian":10,"sc_st":10},
  {"id":133,"name":"Vattiyoorkavu",     "dist":"Thiruvananthapuram", "udf21":38,"ldf21":48,"nda21":12,"inc":"LDF","margin":6200, "minority":12,"ezhava":18,"nair":22,"christian":10,"sc_st":12},
  {"id":134,"name":"Thiruvananthapuram","dist":"Thiruvananthapuram", "udf21":34,"ldf21":44,"nda21":20,"inc":"LDF","margin":6800, "minority":14,"ezhava":16,"nair":20,"christian":12,"sc_st":10},
  {"id":135,"name":"Nemom",             "dist":"Thiruvananthapuram", "udf21":30,"ldf21":41,"nda21":27,"inc":"LDF","margin":7800, "minority":12,"ezhava":18,"nair":20,"christian":14,"sc_st":10},
  {"id":136,"name":"Aruvikkara",        "dist":"Thiruvananthapuram", "udf21":44,"ldf21":43,"nda21":11,"inc":"LDF","margin":600,  "minority":12,"ezhava":20,"nair":22,"christian":10,"sc_st":12},
  {"id":137,"name":"Parassala",         "dist":"Thiruvananthapuram", "udf21":36,"ldf21":44,"nda21":18,"inc":"LDF","margin":5200, "minority":10,"ezhava":22,"nair":22,"christian":10,"sc_st":14},
  {"id":138,"name":"Kattakkada",        "dist":"Thiruvananthapuram", "udf21":38,"ldf21":48,"nda21":12,"inc":"LDF","margin":6400, "minority":10,"ezhava":22,"nair":22,"christian":10,"sc_st":14},
  {"id":139,"name":"Kovalam",           "dist":"Thiruvananthapuram", "udf21":38,"ldf21":47,"nda21":13,"inc":"LDF","margin":5800, "minority":10,"ezhava":20,"nair":22,"christian":10,"sc_st":12},
  {"id":140,"name":"Neyyattinkara",     "dist":"Thiruvananthapuram", "udf21":40,"ldf21":45,"nda21":13,"inc":"LDF","margin":3200, "minority":10,"ezhava":20,"nair":22,"christian":10,"sc_st":14},
]


# ════════════════════════════════════════════════════════════
# CORE SCORING FUNCTION
# ════════════════════════════════════════════════════════════

async def score_constituency_batch(
    seats: list,
    district_signals: dict,
    field_reports: list = None,
) -> list:
    """
    Score a batch using GPT-4o with full P1+P2+Star logic.
    Each seat gets archetype-specific weights + LS 2024 signal + NDA transfer.
    """

    field_summary = {}
    if field_reports:
        for r in field_reports:
            name = r.get("constituency","")
            obs  = r.get("observations","")
            if name and obs:
                field_summary[name] = obs[:200]

    seat_blocks = []
    for s in seats:
        meta  = SEAT_METADATA.get(s["name"], {})
        arch_code = meta.get("arch","NH")
        arch  = ARCHETYPE_CONFIG[arch_code]
        sig   = district_signals.get(s["dist"], DEFAULT_DISTRICT_SIGNALS.get(s["dist"],{}))

        # ════════════════════════════════════════════════════
        # SWING INDEX — Expert Fix (Option A)
        # Merges LS 2024 + LB 2025 + Anti-incumbency into
        # ONE composite signal to eliminate triple-counting
        # ════════════════════════════════════════════════════

        # Step 1: LS component — primary signal, diluted by archetype
        raw_ls_swing  = meta.get("ls24_swing", 0.0)
        ls_winner     = meta.get("ls24_win",   "UDF")
        dilution      = arch["ls_dilution"]
        ls_component  = round(max(min(raw_ls_swing * dilution, 5.0), -4.0), 2)

        # Step 2: LB component — cadre confirmation only (30% weight, max 1.2%)
        lb_component  = round(min(meta.get("lb24", 3), 4) * 0.30, 2)

        # Step 3: Anti-inc component — structural fatigue only (20% weight, max 0.56%)
        ai_component  = round(ANTI_INC_BOOST * 0.20, 2)

        # Step 4: Compose into single Swing Index, hard cap ±5%
        SWING_IDX     = round(max(min(ls_component + lb_component + ai_component, 5.0), -4.0), 2)

        # Step 5: Cadre Resistance — limits conversion in LDF organisational strongholds
        cadre         = CADRE_RESISTANCE.get(s["name"], DEFAULT_CADRE_RESISTANCE)
        eff_swing     = round(SWING_IDX * (1.0 - cadre), 2)

        # Legacy aliases for downstream usage
        diluted_swing = eff_swing
        lb_swing      = lb_component
        anti_inc      = ai_component

        # ── NDA transfer note ───────────────────────────────
        nda_transfer = arch["nda_transfer"]

        # ── Star candidate override ──────────────────────────
        star = STAR_CANDIDATES.get(s["name"])
        star_note = f"⭐ STAR CANDIDATE: {star['note']} → Apply +{star['boost']}% to {star['front'].upper()}" \
                    if star else "No star candidate override for this seat."

        # ── Field report ────────────────────────────────────
        field_note = field_summary.get(s["name"], "No ground report available.")

        seat_blocks.append(
            f"═══ ID:{s['id']} | {s['name']} | {s['dist']} ═══\n"
            f"ARCHETYPE: {arch['name']} ({arch_code})\n"
            f"KEY DRIVER: {arch['key_driver']}\n"
            f"\n2021 BASE: UDF{s['udf21']}% LDF{s['ldf21']}% NDA{s['nda21']}% | Incumbent:{s['inc']} | Margin:{s['margin']:,}\n"
            f"COMMUNITY: Minority{s['minority']}% Ezhava{s['ezhava']}% Nair{s['nair']}% Christian{s['christian']}% SC/ST{s['sc_st']}%\n"
            f"\n━━━ SWING INDEX (single merged signal — do NOT add signals separately) ━━━\n"
            f"  LS component  ({dilution:.2f}x dilution):  {ls_component:+.2f}%\n"
            f"  LB component  (30% weight, max 1.2%):      {lb_component:+.2f}%\n"
            f"  AntiInc comp. (20% weight, residual only): {ai_component:+.2f}%\n"
            f"  SWING INDEX   (hard cap ±5%):              {SWING_IDX:+.2f}%\n"
            f"  Cadre Resist. for {s['name']}:                 {cadre:.0%}\n"
            f"  EFFECTIVE SWING = {SWING_IDX:+.2f} × (1-{cadre:.2f}) = {eff_swing:+.2f}%\n"
            f"  → Apply ONLY this effective swing to 2021 base. Nothing else additive.\n"
            f"  → Cadre resistance protects LDF floor in organisational strongholds.\n"
            f"\nNDA VOTE TRANSFER LOGIC:\n  {nda_transfer}\n"
            f"\nINDEPENDENT SIGNALS (truly separate from wave):\n"
            f"  Inflation={sig.get('inflation',5)}/10 | NDA_surge={sig.get('nda_surge',3)}/10\n"
            f"\n{star_note}\n"
            f"GROUND REPORT: {field_note}"
        )

    prompt = f"""You are Kerala's most experienced electoral data scientist scoring {len(seats)} constituencies for the April 9, 2026 Assembly election.

═══ MACRO CONTEXT (apply to ALL seats) ═══
• Kerala inflation 9.49% — India #1 for 7+ months → independent signal, hurts LDF
• UDF swept 18/20 Lok Sabha 2024 seats — already embedded in Swing Index below
• UDF swept Dec 2025 Local Bodies: 43% vs LDF 40% — already embedded in Swing Index
• LDF seeking unprecedented 3rd consecutive term — 65-year history says NO
• CM race virtually tied: Vijayan 27.85% vs Satheesan 27.77%
• Ezhava (SNDP) drift toward BJP/BDJS — hurts LDF in Ezhava-heavy seats
• Nair (NSS) consolidating toward NDA in South Kerala — affects UDF slightly
• Christian vote → UDF (Church stance, buffer zone issues)
• Minority (Muslim) vote → firmly UDF (IUML machinery strong)
• Rahul Gandhi influence: 44.2% vs Modi 19.5% in Kerala
• Manorama C-Voter (n=89,693): UDF 69-81, LDF 57-69, NDA 1-5
• Political Vibe: NDA 8-17 seats — spoiler role real

═══ SWING INDEX ARCHITECTURE — READ THIS FIRST ═══

Each seat below shows a pre-computed EFFECTIVE SWING.
This is a SINGLE merged signal = LS_component + LB_component + AntiInc_component.

⚠️ DO NOT add any separate LS swing, LB momentum, or anti-incumbency on top.
⚠️ These are already included in the Effective Swing shown per seat.

The ONLY signals to add on top of Effective Swing are:
  → Community composition (Muslim%, Ezhava%, Nair%, Christian% — structural)
  → Inflation signal (truly independent)
  → NDA surge signal (truly independent)
  → NDA transfer logic (archetype-specific)
  → Star candidate override (where applicable)

CADRE RESISTANCE EXPLAINED:
High cadre resistance seats (Dharmadom 90%, Mattanur 85%, Aroor 80%):
  → LDF retains strong organisational floor DESPITE state-wide UDF wave
  → Effective swing already reduced — LDF vote share should remain ≥ 40% here
Low cadre resistance seats (urban corridors, Christian belt, plantation areas):
  → Wave converts more freely to seat flips
  → LDF is genuinely vulnerable here

KERALA FLOOR REALITY — MUST RESPECT:
  LDF organisational minimum: 35+ seats (Kannur 6+, Alappuzha coast 4+, plantation 3+)
  NDA realistic wins: 1-3 seats MAXIMUM (Nemom, Malampuzha most likely)
  UDF realistic range: 75-95 seats

NDA TRANSFER IS NON-LINEAR AND ARCHETYPE-SPECIFIC:
High NDA in minority seats (MM) → hurts UDF.
High NDA in NSS/SNDP seats (NH) → hurts LDF.
High NDA in urban seats (UI) → hurts LDF.

═══ CONSTITUENCY DATA ({len(seats)} seats) ═══
{chr(10).join(seat_blocks)}

═══ SCORING INSTRUCTIONS ═══
For each constituency:
1. Start from 2021 base (structural anchor)
2. Apply EFFECTIVE SWING shown in seat data — this is the ONLY swing signal
   (do NOT add LS, LB, anti-inc separately — already merged and cadre-adjusted)
3. Apply community composition adjustment (independent structural signal)
4. Apply NDA transfer logic if NDA > archetype threshold
5. Apply star candidate override if present (shown in seat data)
6. Apply independent signals: Inflation + NDA surge (shown in seat data)
7. Normalize UDF + LDF + NDA to ~100%

LEAN definition: UDF if udf>ldf+3; LDF if ldf>udf+3; NDA if nda leads both; SWING if gap≤3
RISK: CRITICAL if winning margin implied <3%, HIGH 3-6%, MEDIUM 6-10%, LOW >10%
win_prob_udf: 0-100 probability UDF wins this seat

Return ONLY a JSON array. Each object must have ALL fields:
{{
  "id": <integer>,
  "udf": <integer percentage>,
  "ldf": <integer percentage>,
  "nda": <integer percentage>,
  "lean": "<UDF|LDF|NDA|SWING>",
  "risk": "<CRITICAL|HIGH|MEDIUM|LOW>",
  "win_prob_udf": <integer 0-100>,
  "swing_vs_2021": <float, positive=toward UDF>,
  "rationale": "<2-3 sentences. MUST state: (1) archetype and effective swing applied, (2) cadre resistance impact if >50%, (3) community driver, (4) NDA transfer if applicable>",
  "local_issues": ["<constituency-specific issue 1>","<issue 2>","<issue 3>"],
  "war_room_action": "<specific UDF tactical action for this seat>",
  "key_factor": "<one headline sentence>"
}}"""

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=6000,
            temperature=0.15,
            messages=[
                {"role":"system","content":"Return only valid JSON arrays. No markdown, no extra text. Be politically precise."},
                {"role":"user","content":prompt}
            ]
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  ↳ Batch error: {e}")
        return []


async def score_all_constituencies(
    district_signals: dict = None,
    field_reports: list = None,
) -> list:
    """Score all 140 constituencies in batches of 20."""
    if district_signals is None:
        district_signals = DEFAULT_DISTRICT_SIGNALS

    print(f"\n🎯 Scoring {len(BASE_2021)} constituencies (v3 — P1+P2+Star)")
    print(f"   Swing Index: LS+LB+AntiInc merged (expert fix)")
    print(f"   Anti-inc component: {ANTI_INC_BOOST}% × 20% = {round(ANTI_INC_BOOST*0.2,2)}% (residual only)")
    print(f"   Cadre Resistance: {len(CADRE_RESISTANCE)} seats protected (LDF floor)")
    print(f"   Archetypes: 6 | LS 2024: ✅ | NDA Transfer: ✅ | Stars: {len(STAR_CANDIDATES)}\n")

    batch_size = 20
    all_scores = []

    for i in range(0, len(BASE_2021), batch_size):
        batch     = BASE_2021[i:i+batch_size]
        bn        = i//batch_size+1
        total_batches = (len(BASE_2021)+batch_size-1)//batch_size
        print(f"  ↳ Batch {bn}/{total_batches}: {batch[0]['name']} → {batch[-1]['name']}")

        scores = await score_constituency_batch(batch, district_signals, field_reports)
        score_map = {s["id"]: s for s in scores}

        for seat in batch:
            sid  = seat["id"]
            meta = SEAT_METADATA.get(seat["name"], {})
            arch_code = meta.get("arch","NH")
            star  = STAR_CANDIDATES.get(seat["name"])
            cands = CANDIDATES_2026.get(seat["name"], {"udf":"TBA","ldf":"TBA","nda":"TBA"})

            if sid in score_map:
                sc = score_map[sid]
                # Apply star candidate override on top of GPT-4o score
                udf = sc.get("udf", seat["udf21"])
                ldf = sc.get("ldf", seat["ldf21"])
                nda = sc.get("nda", seat["nda21"])
                if star:
                    front = star["front"]
                    boost = star["boost"]
                    if front == "udf":
                        udf = min(udf + boost, 70)
                        # take from whoever is leading against UDF
                        if ldf > nda: ldf = max(ldf - boost, 15)
                        else: nda = max(nda - boost, 5)
                    elif front == "ldf":
                        ldf = min(ldf + boost, 70)
                        if udf > nda: udf = max(udf - boost, 15)
                        else: nda = max(nda - boost, 5)
                    elif front == "nda":
                        nda = min(nda + boost, 55)
                        # NDA gains from both equally
                        udf = max(udf - boost//2, 15)
                        ldf = max(ldf - (boost - boost//2), 15)

                # Recompute lean after star override
                if nda > udf and nda > ldf:
                    lean = "NDA"
                elif udf > ldf + 3:
                    lean = "UDF"
                elif ldf > udf + 3:
                    lean = "LDF"
                else:
                    lean = "SWING"

                # Recompute risk based on UDF-LDF margin
                margin_pct = abs(udf - ldf)
                if margin_pct < 3:   risk = "CRITICAL"
                elif margin_pct < 6: risk = "HIGH"
                elif margin_pct < 10:risk = "MEDIUM"
                else:                risk = "LOW"

                # ── NDA Spoiler Upgrade ─────────────────────
                # Seats with high NDA are unpredictable
                # regardless of UDF-LDF margin.
                # NDA>=25%: 3-way contest  → force CRITICAL
                # NDA>=20%: spoiler risk   → force min HIGH
                if nda >= 25 and risk in ("MEDIUM", "LOW"):
                    risk = "CRITICAL"
                elif nda >= 20 and risk == "LOW":
                    risk = "HIGH"

                # ── Recompute win_prob after star override + NDA upgrade ──
                # GPT computes win_prob BEFORE star override changes vote shares
                # Recompute from final vote shares for consistency
                import math
                final_margin = udf - ldf
                win_prob_recomputed = round(
                    100 / (1 + math.exp(-final_margin / 4))
                )
                # Blend GPT estimate (40%) with deterministic (60%)
                gpt_prob = sc.get("win_prob_udf", 50)
                win_prob_final = round(gpt_prob * 0.4 + win_prob_recomputed * 0.6)

                all_scores.append({
                    "id":            sid,
                    "name":          seat["name"],
                    "district":      seat["dist"],
                    "archetype":     arch_code,
                    "archetype_name":ARCHETYPE_CONFIG[arch_code]["name"],
                    "udf":           udf,
                    "ldf":           ldf,
                    "nda":           nda,
                    "lean":          lean,
                    "risk":          risk,
                    "win_prob_udf":  win_prob_final,
                    "swing_vs_2021": sc.get("swing_vs_2021", 0),
                    "rationale":     sc.get("rationale","Analysis pending"),
                    "local_issues":  sc.get("local_issues",["Inflation impact","Unemployment","Infrastructure"]),
                    "war_room_action":sc.get("war_room_action","Monitor and maintain ground presence."),
                    "key_factor":    sc.get("key_factor",""),
                    "star_candidate":star["note"] if star else None,
                    "incumbent":     seat["inc"],
                    "margin_2021":   seat["margin"],
                    "minority_pct":  seat["minority"],
                    "ezhava_pct":    seat["ezhava"],
                    "nair_pct":      seat["nair"],
                    "christian_pct": seat["christian"],
                    "sc_st_pct":     seat["sc_st"],
                    "ls24_swing":    meta.get("ls24_swing",0),
                    "ls24_winner":   meta.get("ls24_win","UDF"),
                    "lb24_swing":    meta.get("lb24",0),
                    "candidate_udf": cands["udf"],
                    "candidate_ldf": cands["ldf"],
                    "candidate_nda": cands["nda"],
                })
            else:
                # Fallback: use 2021 + anti-incumbency
                udf = min(seat["udf21"] + ANTI_INC_BOOST, 65)
                ldf = max(seat["ldf21"] - 3, 20)
                nda = seat["nda21"]
                lean = "UDF" if udf > ldf + 3 else "LDF" if ldf > udf + 3 else "SWING"
                all_scores.append({
                    "id":sid,"name":seat["name"],"district":seat["dist"],
                    "archetype":arch_code,"archetype_name":ARCHETYPE_CONFIG[arch_code]["name"],
                    "udf":udf,"ldf":ldf,"nda":nda,"lean":lean,"risk":"MEDIUM",
                    "win_prob_udf":50 if lean=="UDF" else 35,"swing_vs_2021":ANTI_INC_BOOST,
                    "rationale":"2021 base + exponential anti-incumbency (fallback)",
                    "local_issues":["Price rise impact","Unemployment","Development gaps"],
                    "war_room_action":"Maintain standard ground presence + turnout drive",
                    "key_factor":"2021 base + 2-term anti-incumbency",
                    "star_candidate":None,"incumbent":seat["inc"],"margin_2021":seat["margin"],
                    "minority_pct":seat["minority"],"ezhava_pct":seat["ezhava"],
                    "nair_pct":seat["nair"],"christian_pct":seat["christian"],"sc_st_pct":seat["sc_st"],
                    "ls24_swing":meta.get("ls24_swing",0),"ls24_winner":meta.get("ls24_win","UDF"),
                    "lb24_swing":meta.get("lb24",0),
                    "candidate_udf": cands["udf"],
                    "candidate_ldf": cands["ldf"],
                    "candidate_nda": cands["nda"],
                })

        if i + batch_size < len(BASE_2021):
            await asyncio.sleep(2)

    # Summary
    udf   = sum(1 for s in all_scores if s["lean"]=="UDF")
    ldf   = sum(1 for s in all_scores if s["lean"]=="LDF")
    nda   = sum(1 for s in all_scores if s["lean"]=="NDA")
    sw    = sum(1 for s in all_scores if s["lean"]=="SWING")
    crit  = sum(1 for s in all_scores if s["risk"]=="CRITICAL")
    high  = sum(1 for s in all_scores if s["risk"]=="HIGH")
    stars = sum(1 for s in all_scores if s["star_candidate"])

    print(f"\n  ✅ Scoring complete:")
    print(f"     UDF={udf} | LDF={ldf} | NDA={nda} | SWING={sw}")
    print(f"     CRITICAL={crit} | HIGH={high}")
    print(f"     Star overrides applied: {stars}")

    return all_scores


if __name__ == "__main__":
    scores = asyncio.run(score_all_constituencies())
    print(json.dumps(scores[:2], indent=2))