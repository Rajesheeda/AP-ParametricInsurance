"""Post-flood advisory for the 8 classes of the trained pest/disease model (pest_train.py).

Replaces the vision model's free-text advice, which has no source. Each entry is a short summary of the
non-chemical measures in the cited packages of practices, plus why the problem follows floods and cyclones.
Chemical choice and dose are deliberately not given here: they follow the current ANGRAU recommendation through
the AEO, because product registrations and doses change and a label error would be dangerous.
Status: summarised for the POC; to be reviewed by an ANGRAU plant-protection scientist before field use.
"""
RICE = ["DPPQS (Govt of India), Integrated Pest Management Package for Rice",
        "ICAR-IIRR, Rice Knowledge Management Portal (rkmp.co.in)", "ANGRAU, Vyavasaya Panchangam"]
COTTON = ["DPPQS (Govt of India), Integrated Pest Management Package for Cotton",
          "ICAR-CICR, cotton disease management bulletins", "ANGRAU, Vyavasaya Panchangam"]
CHEM = "Chemical control only if the AEO advises it, with the product and dose of the current ANGRAU recommendation."

ADVICE = {
    "paddy bacterial leaf blight": dict(
        why="The bacterium spreads with flood and irrigation water and wind-driven rain; outbreaks often follow cyclones.",
        do=["Drain standing water; do not let water flow from affected fields into healthy ones.",
            "Hold back nitrogen top-dressing while the disease is spreading.",
            "Keep bunds and channels free of grass weeds that carry the bacterium.",
            "After harvest, remove or plough in infected stubble; next season use a tolerant variety and balanced nitrogen."],
        src=RICE),
    "paddy blast": dict(
        why="Long leaf wetness, cloudy humid weather and heavy nitrogen after rain favour blast; neck blast at heading cuts grain filling.",
        do=["Do not apply extra nitrogen now.",
            "Scout leaves and panicle necks every few days, especially at heading.",
            "Remove grass hosts on bunds."],
        src=RICE),
    "paddy brown plant hopper": dict(
        why="Humid weather, a dense canopy and standing water after heavy rain favour hopper build-up at the plant base ('hopper burn').",
        do=["Check the base of the plants (tap test) and act only above the economic threshold in the IPM package.",
            "Drain the field intermittently; open alleyways in dense crop for air movement.",
            "Avoid excess nitrogen.",
            "Avoid synthetic pyrethroids and repeated use of one insecticide: they cause hopper resurgence."],
        src=RICE),
    "paddy brown spot": dict(
        why="A sign of nutrient-stressed crop (potash, silicon, nitrogen) on poor or waterlogged soils; worsens after prolonged wet spells.",
        do=["Drain waterlogged fields.", "Correct potash and nitrogen on the basis of a soil test.",
            "Next season: treated seed and balanced fertiliser."],
        src=RICE),
    "paddy false smut": dict(
        why="Rain and high humidity at flowering, the stage of most Kharif paddy in late October, favour infection of the grains.",
        do=["Remove smut balls carefully into a bag and destroy them, without shaking spores onto healthy panicles.",
            "Avoid extra nitrogen.", "Harvest badly affected patches separately so seed is not contaminated.",
            "Next season: preventive protection at the boot-leaf stage as ANGRAU recommends."],
        src=RICE),
    "paddy sheath blight": dict(
        why="A dense canopy, standing water and high humidity after heavy rain spread it up the sheaths from the water line.",
        do=["Drain and keep water shallow.", "Avoid extra nitrogen.", "Remove weed hosts on bunds."],
        src=RICE),
    "cotton bacterial blight": dict(
        why="Spread by rain splash and wind-driven rain; leaf and boll infection rise after storms.",
        do=["Improve drainage; avoid working in the crop while it is wet.", "Remove and destroy infected plant debris.",
            "Next season: delinted, treated seed and a tolerant variety."],
        src=COTTON),
    "cotton alternaria leaf spot": dict(
        why="Wet, humid weather late in the season and potassium deficiency favour it; leaves drop early.",
        do=["Drain waterlogged patches.", "Correct potassium on the basis of a soil test.", "Remove fallen infected leaves."],
        src=COTTON),
}


def advice(label):
    a = ADVICE.get(label)
    return None if a is None else dict(label=label, why=a["why"], actions=a["do"] + [CHEM], sources=a["src"],
                                       status="summarised from the cited packages; ANGRAU review pending")
