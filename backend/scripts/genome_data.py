"""The Gap Genome's chains, written by hand: what each JEE / NEET chapter really rests on, from real NCERT chapters only.

The AI writes these when a key is set (scripts/warm_chains.py). These are the same shape, written and checked by hand,
so the demo needs no AI and every link is one a teacher would sign off: each goes DOWN through the classes, names the
exact idea the chapter supplies, and carries one question that checks it (answer index 0-3).

LINKS: one entry per earlier idea (chapter id, the idea, its check question, and, for the ideas the demo can land on,
a five-minute lesson in English with a fresh question). CHAINS: exam chapter -> [(link, why the topic needs it)],
closest first. scripts/seed_showcase.py loads both into the shared tables the app already reads.
"""
from __future__ import annotations

from typing import Any


def q(text: str, options: list[str], answer: int, explain: str) -> dict[str, Any]:
    assert len(options) == 4 and 0 <= answer < 4
    return {"q": text, "options": options, "answer": answer, "explain": explain}


LINKS: dict[str, dict[str, Any]] = {
    # ------------------------------------------------------------------ mathematics
    "trig10": {
        "chapter_id": "c10.mathematics.introduction-to-trigonometry", "idea": "sin and cos of an angle, and components",
        "check": q("A 10 N force acts at 30° to the horizontal. Its horizontal part is…",
                   ["5 N", "$5\\sqrt{3}$ N", "10 N", "$10\\sqrt{3}$ N"], 1, "Horizontal part = 10 cos 30° = $5\\sqrt{3}$ N"),
        "lesson": '**Any slanted quantity can be split into two perpendicular parts.** A force or velocity at angle θ has a component $F\\cos\\theta$ along the reference direction and $F\\sin\\theta$ perpendicular to it.\n\n**Example from daily life:** When you pull a cart with a rope held at 60°, only $F\\cos 60° = F/2$ moves it forward; the rest pulls upward.\n\n**Worked example:** A 20 N force at 30°: forward part $20\\cos30° = 10\\sqrt3$ N, upward part $20\\sin30° = 10$ N.\n\nRemember: $\\sin 0° = 0$ and $\\sin 90° = 1$, so a force has its full turning effect only when it acts perpendicular to the lever.',
        "fix": q("A spanner is pushed with 40 N at 90° to it. The part of the force that turns it is…",
                 ["0 N", "20 N", "40 N", "$40\\sqrt2$ N"], 2, "Turning part = 40 sin 90° = 40 N"),
    },
    "triangles10": {
        "chapter_id": "c10.mathematics.triangles", "idea": "similar triangles and ratio of sides",
        "check": q("Two similar triangles have sides in the ratio 2 : 3. If a side of the smaller is 4 cm, the matching side of the larger is…",
                   ["5 cm", "6 cm", "8 cm", "12 cm"], 1, "4 × 3/2 = 6 cm"),
    },
    "coord10": {
        "chapter_id": "c10.mathematics.coordinate-geometry", "idea": "distance between two points",
        "check": q("The distance between (1, 2) and (4, 6) is…", ["3", "4", "5", "7"], 2, "√(3² + 4²) = 5"),
    },
    "quad10": {
        "chapter_id": "c10.mathematics.quadratic-equations", "idea": "roots and the discriminant",
        "check": q("$x^2 - 5x + 6 = 0$ has roots…", ["1 and 6", "2 and 3", "−2 and −3", "no real roots"], 1, "(x − 2)(x − 3) = 0"),
    },
    "prob10": {
        "chapter_id": "c10.mathematics.probability-class-10", "idea": "probability as favourable over total",
        "check": q("A fair die is thrown. The probability of an even number is…", ["1/6", "1/3", "1/2", "2/3"], 2, "3 even faces out of 6 = 1/2"),
    },
    "slope9": {
        "chapter_id": "c9.mathematics.two-variables-one-line", "idea": "slope of a straight-line graph",
        "check": q("A line passes through (0, 2) and (4, 10). Its slope is…", ["2", "4", "8", "1/2"], 0, "(10 − 2)/(4 − 0) = 2"),
        "lesson": '**Slope measures how much y changes for each unit change in x:** slope $= \\dfrac{\\Delta y}{\\Delta x}$.\n\n**Example from daily life:** If a metro fare rises by ₹5 per station, the graph of fare against stations is a straight line with slope 5.\n\n**Worked example:** The line through (1, 3) and (3, 11) has slope $(11-3)/(3-1) = 4$.\n\nIn physics, the slope of an x–t graph is velocity, and the slope of a v–t graph is acceleration.',
        "fix": q("On a v–t graph, velocity goes from 4 m/s to 16 m/s in 3 s along a straight line. The acceleration is…",
                 ["3 m/s²", "4 m/s²", "12 m/s²", "48 m/s²"], 1, "slope = (16 − 4)/3 = 4"),
    },
    "identities9": {
        "chapter_id": "c9.mathematics.exploring-algebraic-identities", "idea": "(a+b)², (a−b)² and a² − b²",
        "check": q("$51^2 - 49^2$ equals…", ["2", "100", "200", "400"], 2, "(51 + 49)(51 − 49) = 200"),
    },
    "linpoly9": {
        "chapter_id": "c9.mathematics.introduction-to-linear-polynomials", "idea": "rearranging a linear equation for one unknown",
        "check": q("If $V = IR$, then $R$ equals…", ["$VI$", "$V/I$", "$I/V$", "$V - I$"], 1, "Divide both sides by I"),
        "lesson": '**An equation is a balance.** Whatever you do to one side, do to the other. To isolate an unknown, undo each operation attached to it.\n\n**Example from daily life:** A ₹299 plan lasting 28 days costs $299/28$ per day: the same step of dividing both sides.\n\n**Worked example:** From $P = VI$, divide both sides by $V$ to get $I = P/V$.\n\nEvery circuit problem relies on this: $V = IR$ gives $I = V/R$ or $R = V/I$, with no memorisation needed.',
        "fix": q("If $P = I^2 R$, then $I$ equals…", ["$P/R$", "$\\sqrt{P/R}$", "$PR$", "$\\sqrt{PR}$"], 1, "I² = P/R, so I = √(P/R)"),
    },
    "coords9": {
        "chapter_id": "c9.mathematics.orienting-yourself-the-use-of-coordinates", "idea": "plotting points on x and y axes",
        "check": q("The point (−3, 2) lies in which quadrant?", ["First", "Second", "Third", "Fourth"], 1, "x negative, y positive"),
    },
    "pythag8": {
        "chapter_id": "c8.mathematics.the-baudhayana-pythagoras-theorem", "idea": "a² + b² = c² in a right triangle",
        "check": q("A right triangle has legs 6 and 8. Its hypotenuse is…", ["10", "12", "14", "48"], 0, "√(36 + 64) = 10"),
    },
    "power8": {
        "chapter_id": "c8.mathematics.power-play", "idea": "powers of ten and the laws of exponents",
        "check": q("$\\dfrac{10^{-6}}{10^{-9}}$ equals…", ["$10^{-15}$", "$10^{-3}$", "$10^{3}$", "$10^{15}$"], 2, "−6 − (−9) = 3"),
        "lesson": "**With the same base, add or subtract the powers:** $a^m \\times a^n = a^{m+n}$, $a^m / a^n = a^{m-n}$, and $a^{-n} = 1/a^n$.\n\n**Example from daily life:** 1 km $= 10^3$ m and 1 mm $= 10^{-3}$ m, so 1 km contains $10^3 / 10^{-3} = 10^6$ mm.\n\n**Worked example:** $9\\times10^9 \\times 2\\times10^{-6} = 18\\times10^{3}$.\n\nCoulomb's law uses $k = 9\\times10^9$ with charges in µC, so this skill appears in almost every question.",
        "fix": q("$(2\\times10^{-3})^2$ equals…", ["$4\\times10^{-6}$", "$4\\times10^{-5}$", "$2\\times10^{-6}$", "$4\\times10^{6}$"], 0,
                 "2² × 10^(−3×2) = 4 × 10⁻⁶"),
    },
    "prop1_8": {
        "chapter_id": "c8.mathematics.proportional-reasoning-1", "idea": "ratios and direct proportion",
        "check": q("If 4 pens cost ₹60, then 7 pens cost…", ["₹90", "₹105", "₹120", "₹420"], 1, "60/4 × 7 = 105"),
    },
    "invprop8": {
        "chapter_id": "c8.mathematics.proportional-reasoning-2", "idea": "inverse proportion: one doubles, the other halves",
        "check": q("If $F \\propto 1/r^2$ and r is doubled, F becomes…", ["2F", "F/2", "F/4", "4F"], 2, "1/2² = 1/4"),
        "lesson": "**In inverse proportion, as one quantity grows the other shrinks by the same factor.** If $y \\propto 1/x$, doubling $x$ halves $y$. If $y \\propto 1/x^2$, doubling $x$ makes $y$ one quarter.\n\n**Example from daily life:** Move twice as far from a lamp and the light reaching you falls to a quarter.\n\n**Worked example:** $F \\propto 1/r^2$; tripling $r$ makes the force $F/9$.\n\nBoth Coulomb's law and Newton's law of gravitation follow this inverse-square pattern.",
        "fix": q("If $E \\propto 1/r^2$ and r is halved, E becomes…", ["E/4", "E/2", "2E", "4E"], 3, "1/(1/2)² = 4"),
    },
    "area8": {
        "chapter_id": "c8.mathematics.area", "idea": "area of rectangles, triangles and trapeziums",
        "check": q("A trapezium has parallel sides 4 and 6 and height 2. Its area is…", ["10", "12", "20", "24"], 0, "½ × (4 + 6) × 2 = 10"),
    },
    "fractions7": {
        "chapter_id": "c7.mathematics.working-with-fractions", "idea": "multiplying and dividing fractions",
        "check": q("$\\dfrac{3}{4} \\times \\dfrac{2}{9}$ equals…", ["1/6", "5/13", "6/13", "3/2"], 0, "6/36 = 1/6"),
    },
    "integers7": {
        "chapter_id": "c7.mathematics.operations-with-integers", "idea": "signs when multiplying negatives",
        "check": q("(−3) × (−4) − 5 equals…", ["−17", "−7", "7", "17"], 2, "12 − 5 = 7"),
    },
    "decimals7": {
        "chapter_id": "c7.mathematics.a-peek-beyond-the-point", "idea": "decimals and place value",
        "check": q("0.25 + 0.5 equals…", ["0.30", "0.75", "0.255", "7.5"], 1, "0.25 + 0.50 = 0.75"),
    },
    "angles6": {
        "chapter_id": "c6.mathematics.lines-and-angles", "idea": "measuring angles and perpendicular lines",
        "check": q("The angle between two perpendicular lines is…", ["0°", "45°", "90°", "180°"], 2, "Perpendicular means 90°"),
        "lesson": "**An angle measures how far one line turns from another.** A straight line is 180°, perpendicular lines meet at 90°, and a full turn is 360°.\n\n**Example from daily life:** At 3 o'clock the hands of a clock are at 90°; at 6 o'clock they are at 180°.\n\n**Worked example:** Two angles on a straight line add to 180°, so the partner of 65° is 115°.\n\nTorque depends on this angle: a force turns a lever most effectively at 90° to it.",
        "fix": q("Two angles on a straight line are x and 3x. Then x is…", ["30°", "45°", "60°", "90°"], 1, "4x = 180°, x = 45°"),
    },
    # ------------------------------------------------------------------ science (physics)
    "elec10": {
        "chapter_id": "c10.science.electricity", "idea": "potential difference, Ohm's law and resistors in series / parallel",
        "check": q("Two 6 Ω resistors are joined in parallel. Together they make…", ["3 Ω", "6 Ω", "12 Ω", "36 Ω"], 0,
                   "1/R = 1/6 + 1/6, R = 3 Ω"),
        "lesson": "**Current is the flow of charge; potential difference is what drives it.** Ohm's law: $V = IR$. A larger resistance means a smaller current.\n\n**Series:** one after another, so $R = R_1 + R_2$. **Parallel:** side by side, so $\\dfrac1R = \\dfrac1{R_1} + \\dfrac1{R_2}$, and the total is always less than the smallest resistor.\n\n**Example from daily life:** Household lamps are wired in parallel, so each receives the full 220 V and one failing does not switch off the others.\n\n**Worked example:** 4 Ω and 12 Ω in parallel: $1/R = 1/4 + 1/12 = 4/12$, so $R = 3$ Ω. Across 6 V, $I = 6/3 = 2$ A.\n\nKirchhoff's laws, electric potential and capacitors all build on this idea.",
        "fix": q("A 3 Ω and a 6 Ω resistor are in parallel across 12 V. The total current is…", ["1.3 A", "2 A", "4 A", "6 A"], 3,
                 "R = 2 Ω, I = 12/2 = 6 A"),
    },
    "magfx10": {
        "chapter_id": "c10.science.magnetic-effects-of-electric-current", "idea": "the field around a current and the right-hand thumb rule",
        "check": q("Current flows up a vertical wire. Seen from above, the magnetic field lines go…",
                   ["Clockwise", "Anticlockwise", "Straight up", "Straight down"], 1, "Right thumb up, fingers curl anticlockwise"),
        "lesson": "**Wherever a current flows, it creates a magnetic field.** Around a straight wire the field forms concentric circles.\n\n**Right-hand thumb rule:** point your thumb along the current; your curled fingers show the direction of the field.\n\n**Example from daily life:** A compass needle placed near a current-carrying wire deflects, as Oersted first observed.\n\n**Worked example:** For a current flowing downward, the field seen from above is clockwise.\n\nThe Biot–Savart law and Ampère's law turn these circles into numbers.",
        "fix": q("Current flows down a vertical wire. Seen from above, the field lines go…",
                 ["Clockwise", "Anticlockwise", "Radially out", "No field"], 0, "Right thumb down, fingers curl clockwise"),
    },
    "light10": {
        "chapter_id": "c10.science.light-reflection-and-refraction", "idea": "the mirror / lens formula and sign convention",
        "check": q("A concave mirror has focal length 10 cm. An object at 30 cm forms its image at…", ["7.5 cm", "15 cm", "20 cm", "30 cm"], 1,
                   "1/v = 1/10 − 1/30 = 2/30, v = 15 cm in front"),
    },
    "motion9": {
        "chapter_id": "c9.science.describing-motion-around-us", "idea": "velocity, acceleration and v = u + at",
        "check": q("A bike starts from rest and reaches 20 m/s in 5 s. Its acceleration is…", ["2 m/s²", "4 m/s²", "25 m/s²", "100 m/s²"], 1,
                   "a = (20 − 0)/5 = 4 m/s²"),
        "lesson": '**Velocity is the rate of change of position; acceleration is the rate of change of velocity.** $v = u + at$: the final velocity equals the initial velocity plus the change per second multiplied by time.\n\n**Example from daily life:** A metro train reaching 20 m/s from rest in 10 s gains 2 m/s every second, so $a = 2$ m/s².\n\n**Worked example:** $u = 5$ m/s, $a = 3$ m/s², $t = 4$ s gives $v = 5 + 12 = 17$ m/s.\n\nMotion graphs and projectile motion are both built on these definitions.',
        "fix": q("A car at 30 m/s brakes at 5 m/s². It stops after…", ["3 s", "5 s", "6 s", "150 s"], 2, "0 = 30 − 5t, t = 6 s"),
    },
    "forces9": {
        "chapter_id": "c9.science.how-forces-affect-motion", "idea": "net force, F = ma and balanced forces",
        "check": q("A 2 kg box is pushed with 10 N against 4 N of friction. Its acceleration is…", ["2 m/s²", "3 m/s²", "5 m/s²", "7 m/s²"], 1,
                   "Net 6 N, a = 6/2 = 3 m/s²"),
        "lesson": "**An object's velocity changes only when there is a net force on it.** Add all the forces, taking direction into account; the result is the net force, and $a = F_{net}/m$.\n\n**Example from daily life:** In a tug-of-war between equally strong teams the rope does not move: the forces are balanced and the net force is zero.\n\n**Worked example:** A 5 kg trolley with 30 N forward and 10 N of friction has a net force of 20 N, so $a = 4$ m/s².\n\nRotation follows the same rule: $\\tau_{net} = I\\alpha$, with torque in place of force and moment of inertia in place of mass.",
        "fix": q("A 4 kg block has 12 N pulling right and 12 N pulling left. Its acceleration is…", ["0", "3 m/s²", "6 m/s²", "24 m/s²"], 0,
                 "Balanced forces: net force 0"),
    },
    "work9": {
        "chapter_id": "c9.science.work-energy-and-simple-machines", "idea": "work done, kinetic and potential energy",
        "check": q("A 2 kg ball moves at 3 m/s. Its kinetic energy is…", ["3 J", "6 J", "9 J", "18 J"], 2, "½ × 2 × 3² = 9 J"),
    },
    "sound9": {
        "chapter_id": "c9.science.sound-waves-characteristics-and-applications", "idea": "frequency, wavelength and v = fλ",
        "check": q("A sound of 340 Hz travels at 340 m/s. Its wavelength is…", ["0.5 m", "1 m", "2 m", "340 m"], 1, "λ = 340/340 = 1 m"),
    },
    "circuit7": {
        "chapter_id": "c7.science.electricity-circuits-and-their-components", "idea": "a closed circuit and how current flows in it",
        "check": q("A bulb, a cell and a switch are in one loop. With the switch open, the bulb…",
                   ["Glows dimly", "Glows fully", "Does not glow", "Glows only briefly"], 2, "An open switch breaks the loop"),
        "lesson": "**Current flows only around a complete, closed loop:** out of the cell's positive terminal, through every component, and back to the negative terminal. Break the loop anywhere and the current stops.\n\n**Example from daily life:** Switching off a fan breaks the loop, so it stops immediately.\n\n**Worked example:** If two bulbs are in series and one fails, both go out because the loop is broken.\n\nKirchhoff's loop law expresses the same idea: around any closed loop, the potential differences must balance.",
        "fix": q("Two bulbs are in series in one loop. One bulb burns out. The other…", ["Glows brighter", "Glows the same", "Goes off", "Flickers"], 2,
                 "The loop is broken, so no current flows"),
    },
    "light8": {
        "chapter_id": "c8.science.light-mirrors-and-lenses", "idea": "the laws of reflection",
        "check": q("A ray hits a plane mirror at 40° to the normal. It reflects at…", ["40°", "50°", "80°", "90°"], 0, "Angle of incidence = angle of reflection"),
    },
    "pressure8": {
        "chapter_id": "c8.science.pressure-winds-storms-and-cyclones", "idea": "air moves from high to low pressure",
        "check": q("Air always flows from…", ["Low to high pressure", "High to low pressure", "Cold to hot only", "Up to down only"], 1,
                   "A pressure difference pushes air from high to low"),
    },
    "magnets6": {
        "chapter_id": "c6.science.exploring-magnets", "idea": "poles of a magnet and its field lines",
        "check": q("Outside a bar magnet, field lines go from…", ["N to S", "S to N", "Middle to the ends", "Nowhere: they are closed inside"], 0,
                   "Outside the magnet, lines leave N and enter S"),
        "lesson": '**Every magnet has two poles, north and south.** Like poles repel and unlike poles attract. Outside the magnet, field lines run from north to south.\n\n**Example from daily life:** Turn a fridge magnet around and it pushes away from another magnet instead of sticking.\n\n**Worked example:** Two magnets placed north to north repel.\n\nA current-carrying loop behaves like a small magnet with a north face and a south face, which is where the study of magnetism begins.',
        "fix": q("Two bar magnets are placed with N facing S. They…", ["Repel", "Attract", "Do nothing", "Spin"], 1, "Unlike poles attract"),
    },
    # ------------------------------------------------------------------ science (chemistry)
    "reactions10": {
        "chapter_id": "c10.science.chemical-reactions-and-equations", "idea": "balancing equations and oxidation / reduction",
        "check": q("In $CuO + H_2 \\rightarrow Cu + H_2O$, the substance oxidised is…", ["CuO", "$H_2$", "Cu", "$H_2O$"], 1,
                   "H₂ gains oxygen, so it is oxidised"),
        "lesson": '**Oxidation is the gain of oxygen (or loss of hydrogen); reduction is the loss of oxygen (or gain of hydrogen).** The two always occur together.\n\n**Example from daily life:** Rusting is the oxidation of iron.\n\n**Worked example:** In $ZnO + C \\rightarrow Zn + CO$, ZnO is reduced (it loses oxygen) and carbon is oxidised.\n\nRedox chemistry and electrochemistry describe the same process in terms of electrons: losing electrons is oxidation.',
        "fix": q("In $ZnO + C \\rightarrow Zn + CO$, the substance reduced is…", ["ZnO", "C", "Zn", "CO"], 0, "ZnO loses oxygen"),
    },
    "acids10": {
        "chapter_id": "c10.science.acids-bases-and-salts", "idea": "pH and acids versus bases",
        "check": q("A solution has pH 3. It is…", ["Strongly basic", "Neutral", "Acidic", "Weakly basic"], 2, "pH below 7 is acidic"),
    },
    "carbon10": {
        "chapter_id": "c10.science.carbon-and-its-compounds", "idea": "covalent bonds and functional groups",
        "check": q("The functional group in ethanol is…", ["–COOH", "–OH", "–CHO", "C=O"], 1, "Ethanol is an alcohol: –OH"),
    },
    "metals10": {
        "chapter_id": "c10.science.metals-and-non-metals", "idea": "ionic bonds and the reactivity series",
        "check": q("NaCl is held together by…", ["Covalent bonds", "Ionic bonds", "Metallic bonds", "Hydrogen bonds"], 1,
                   "Na gives an electron to Cl: ions"),
    },
    "heredity10": {
        "chapter_id": "c10.science.heredity", "idea": "dominant and recessive traits (Mendel)",
        "check": q("Tt × Tt: the fraction of offspring that are tt is…", ["0", "1/4", "1/2", "3/4"], 1, "TT : Tt : tt = 1 : 2 : 1"),
    },
    "lifeproc10": {
        "chapter_id": "c10.science.life-processes", "idea": "nutrition and respiration in living things",
        "check": q("Aerobic respiration releases energy from glucose using…", ["Nitrogen", "Oxygen", "Carbon dioxide", "Light"], 1,
                   "Glucose + O₂ → CO₂ + H₂O + energy"),
    },
    "reproduce10": {
        "chapter_id": "c10.science.how-do-organisms-reproduce", "idea": "sexual reproduction and gametes",
        "check": q("A human gamete has how many chromosomes?", ["23", "46", "44", "92"], 0, "Gametes are haploid: 23"),
    },
    "atom9": {
        "chapter_id": "c9.science.journey-inside-the-atom", "idea": "electrons in shells and valency",
        "check": q("Sodium (atomic number 11) has electron shells…", ["2, 8, 1", "2, 9", "2, 8, 8", "8, 2, 1"], 0, "2 + 8 + 1 = 11"),
        "lesson": '**Electrons occupy shells: up to 2 in the first, 8 in the second and 8 in the third (at the Class 9 level).** The outermost (valence) electrons take part in bonding.\n\n**Example from daily life:** Like seats on a bus, the front rows fill before the back rows.\n\n**Worked example:** Chlorine (atomic number 17) is 2, 8, 7. It needs one more electron, so its valency is 1.\n\nChemical bonding and periodic trends all follow from the outermost shell.',
        "fix": q("Chlorine has atomic number 17. Its valency is…", ["1", "2", "7", "17"], 0, "2, 8, 7: needs one more electron"),
    },
    "mole9": {
        "chapter_id": "c9.science.atomic-foundations-of-matter", "idea": "atomic mass and the mole",
        "check": q("How many moles are in 36 g of water (H₂O = 18 g/mol)?", ["0.5", "1", "2", "18"], 2, "36/18 = 2 mol"),
        "lesson": '**A mole is a counting unit, like a dozen but far larger: $6.022\\times10^{23}$ particles.** The mass of one mole of a substance is its molar mass in grams.\n\n**Example from daily life:** Eggs are counted in dozens; atoms are counted in moles.\n\n**Worked example:** 44 g of CO₂ (molar mass 44 g/mol) is 1 mol, or $6.022\\times10^{23}$ molecules.\n\nStoichiometry and the molarity of solutions all begin with moles = mass ÷ molar mass.',
        "fix": q("How many moles are in 88 g of CO₂ (44 g/mol)?", ["0.5", "1", "2", "4"], 2, "88/44 = 2 mol"),
    },
    "cell9": {
        "chapter_id": "c9.science.cell-the-building-block-of-life", "idea": "the nucleus, chromosomes and cell organelles",
        "check": q("Genetic material in a cell is mostly found in the…", ["Cell wall", "Nucleus", "Vacuole", "Ribosome"], 1,
                   "DNA is in the chromosomes in the nucleus"),
    },
    "reprod9": {
        "chapter_id": "c9.science.reproduction-how-life-continues", "idea": "how cells and organisms reproduce",
        "check": q("Making an exact copy of a cell for growth is…", ["Fertilisation", "Cell division", "Pollination", "Digestion"], 1,
                   "Cells divide to grow and repair"),
    },
    "particles8": {
        "chapter_id": "c8.science.particulate-nature-of-matter", "idea": "matter is made of tiny moving particles",
        "check": q("Smell of food spreads across a room because particles…", ["Stop moving", "Diffuse", "Get bigger", "Turn into light"], 1,
                   "Particles keep moving and spread out"),
    },
    "solutions8": {
        "chapter_id": "c8.science.the-amazing-world-of-solutes-solvents-and-solutions", "idea": "solute, solvent and concentration",
        "check": q("In sugar water, the solvent is…", ["Sugar", "Water", "Both", "Neither"], 1, "Water dissolves the sugar"),
    },
    "plants7": {
        "chapter_id": "c7.science.life-processes-in-plants", "idea": "photosynthesis needs light, water and CO₂",
        "check": q("Plants make food in the presence of…", ["Darkness only", "Sunlight", "Soil only", "Oxygen only"], 1,
                   "Photosynthesis needs sunlight"),
    },
    "animals7": {
        "chapter_id": "c7.science.life-processes-in-animals", "idea": "breathing and the lungs",
        "check": q("When we breathe in, the diaphragm…", ["Moves up", "Moves down", "Does not move", "Leaves the chest"], 1,
                   "It moves down so the chest gets bigger"),
    },
    "adolescence7": {
        "chapter_id": "c7.science.adolescence-a-stage-of-growth-and-change", "idea": "hormones and changes at puberty",
        "check": q("Changes at puberty are controlled by…", ["Hormones", "Vitamins", "Enzymes only", "Minerals"], 0, "Hormones cause the changes"),
    },
}

# exam chapters that are also links (a later chapter that rests on an earlier one of the same exam)
for _cid, _name, _cls, _subject, _idea, _check in (
    ("physics.kinematics", "Kinematics", 11, "Physics", "velocity, acceleration and their graphs",
     q("A ball is thrown up at 20 m/s (g = 10 m/s²). It reaches the top after…", ["1 s", "2 s", "4 s", "20 s"], 1, "0 = 20 − 10t, t = 2 s")),
    ("mathematics.straight-lines", "Straight Lines", 11, "Mathematics", "the equation of a line and its slope",
     q("The slope of $2x + y = 6$ is…", ["−2", "2", "6", "−1/2"], 0, "y = −2x + 6")),
    ("mathematics.permutations-and-combinations", "Permutations & Combinations", 11, "Mathematics", "counting arrangements and selections",
     q("$^5C_2$ equals…", ["10", "20", "25", "60"], 0, "5·4/2 = 10")),
    ("mathematics.sets-relations-and-functions", "Sets, Relations & Functions", 11, "Mathematics", "what a function is: one input, one output",
     q("If $f(x) = 2x + 1$, then $f(3)$ is…", ["5", "6", "7", "9"], 2, "2·3 + 1 = 7")),
    ("mathematics.limits-continuity-and-differentiability", "Limits, Continuity & Differentiability", 12, "Mathematics",
     "the derivative as a rate of change", q("The derivative of $x^3$ is…", ["$x^2$", "$3x^2$", "$3x$", "$x^4/4$"], 1, "d/dx xⁿ = n xⁿ⁻¹")),
    ("biology.cell-the-unit-of-life", "Cell: The Unit of Life", 11, "Biology", "cell organelles and their jobs",
     q("The 'powerhouse of the cell' is the…", ["Ribosome", "Mitochondrion", "Golgi body", "Lysosome"], 1, "Mitochondria make ATP")),
    ("biology.biomolecules", "Biomolecules", 11, "Biology", "nucleotides: sugar, phosphate and base",
     q("A nucleotide does NOT contain…", ["A sugar", "A phosphate", "A nitrogen base", "A fatty acid"], 3, "Sugar + phosphate + base")),
):
    LINKS[_cid] = {"chapter_id": _cid, "name": _name, "cls": _cls, "subject": _subject, "idea": _idea, "check": _check}

LINKS["physics.kinematics"]["lesson"] = "**Kinematics answers three questions: where an object is, how fast it is moving, and how its speed is changing.** An object thrown upward loses $g = 10$ m/s of speed every second and is momentarily at rest at the top.\n\n**Example from daily life:** A cricket ball hit straight up slows on the way up, stops for an instant, then speeds up on the way down.\n\n**Worked example:** Thrown up at 30 m/s, it reaches the top after $t = 30/10 = 3$ s.\n\nNewton's laws connect this acceleration to force: $F = ma$."
LINKS["physics.kinematics"]["fix"] = q("A stone is thrown up at 30 m/s (g = 10 m/s²). Its speed after 1 s is…",
                                       ["10 m/s", "20 m/s", "30 m/s", "40 m/s"], 1, "30 − 10·1 = 20 m/s")

CHAINS: dict[str, list[tuple[str, str]]] = {
    # ------------------------------------------------------------------ physics
    "physics.kinematics": [("trig10", "Projectiles split the velocity into u cos θ and u sin θ"),
                           ("motion9", "Every kinematics equation grows out of v = u + at"),
                           ("slope9", "Velocity is the slope of x–t, acceleration the slope of v–t")],
    "physics.laws-of-motion": [("physics.kinematics", "F = ma needs acceleration first"),
                               ("trig10", "Forces on an incline are split with sin θ and cos θ"),
                               ("forces9", "Free-body diagrams are net force and F = ma")],
    "physics.work-energy-and-power": [("trig10", "W = Fd cos θ"), ("work9", "The work–energy theorem is Class 9 KE and PE, made exact"),
                                      ("identities9", "v² − u² = 2as is where ΔKE comes from")],
    "physics.rotational-motion": [("trig10", "Torque = rF sin θ"), ("forces9", "τ = Iα is F = ma for turning"),
                                  ("angles6", "Torque is largest when the force is at 90° to the lever")],
    "physics.gravitation": [("forces9", "Weight and orbits are F = ma with gravity as the force"),
                            ("power8", "G = 6.67 × 10⁻¹¹ and Earth's mass need powers of ten"),
                            ("invprop8", "F ∝ 1/r²: double the distance, a quarter of the force")],
    "physics.oscillations-and-waves": [("trig10", "SHM is x = A sin ωt"), ("sound9", "Waves use v = fλ throughout"),
                                       ("prop1_8", "Period, frequency and speed are ratios")],
    "physics.electrostatics": [("elec10", "Potential and capacitors start from potential difference and V = W/q"),
                               ("power8", "k = 9 × 10⁹ and µC charges are powers of ten"),
                               ("invprop8", "Coulomb's law: F ∝ 1/r²")],
    "physics.current-electricity": [("elec10", "Kirchhoff's laws are Ohm's law and series / parallel at every node"),
                                    ("linpoly9", "Every circuit question is V = IR rearranged"),
                                    ("circuit7", "Current needs a closed loop")],
    "physics.magnetic-effects-of-current-and-magnetism": [("magfx10", "Biot–Savart counts the field around a current"),
                                                          ("elec10", "The field depends on the current in the circuit"),
                                                          ("magnets6", "A current loop is a magnet with an N and an S face")],
    "physics.electromagnetic-induction-and-ac": [("magfx10", "Changing that field is what induces an EMF"),
                                                 ("trig10", "AC is V₀ sin ωt"), ("elec10", "Impedance builds on resistance and Ohm's law")],
    "physics.ray-and-wave-optics": [("light10", "Every lens and mirror question uses 1/v ± 1/u = 1/f with signs"),
                                    ("trig10", "Snell's law: n₁ sin i = n₂ sin r"), ("light8", "Ray diagrams start from the laws of reflection")],
    # ------------------------------------------------------------------ chemistry
    "chemistry.some-basic-concepts-of-chemistry": [("mole9", "Stoichiometry is moles = mass / molar mass"),
                                                   ("prop1_8", "Limiting reagents and % composition are ratios"),
                                                   ("decimals7", "Molar masses and answers are decimals")],
    "chemistry.atomic-structure": [("atom9", "Quantum numbers fill the same shells, in more detail"),
                                   ("particles8", "An atom is the particle matter is made of"),
                                   ("power8", "Wavelengths and energies are in powers of ten")],
    "chemistry.chemical-bonding-and-molecular-structure": [("metals10", "Ionic bonding is electron transfer"),
                                                           ("carbon10", "Covalent bonding is electron sharing"),
                                                           ("atom9", "Bonds are made by valence electrons")],
    "chemistry.equilibrium": [("acids10", "Ionic equilibrium is pH, made exact"), ("power8", "Kₐ = 1.8 × 10⁻⁵ and pH = −log[H⁺]"),
                              ("prop1_8", "K is a ratio of concentrations")],
    "chemistry.chemical-kinetics": [("reactions10", "Rate laws need the balanced equation"),
                                    ("slope9", "Rate is the slope of concentration vs time"),
                                    ("power8", "Rate constants and half-lives are powers of ten")],
    "chemistry.redox-reactions-and-electrochemistry": [("reactions10", "Redox is oxidation and reduction, by electrons"),
                                                       ("elec10", "A cell's EMF is a potential difference"),
                                                       ("metals10", "The electrochemical series is the reactivity series")],
    "chemistry.solutions": [("mole9", "Molarity and molality are moles per volume or mass"),
                            ("solutions8", "Solute and solvent come first"), ("prop1_8", "Mass % and ppm are ratios")],
    "chemistry.general-organic-chemistry": [("carbon10", "GOC starts from functional groups and homologous series"),
                                            ("atom9", "Inductive and resonance effects are valence electrons moving")],
    # ------------------------------------------------------------------ mathematics
    "mathematics.trigonometry": [("trig10", "Every identity grows from sin, cos and tan"),
                                 ("triangles10", "Trig ratios exist because similar triangles keep their ratios"),
                                 ("pythag8", "sin²θ + cos²θ = 1 is Pythagoras")],
    "mathematics.quadratic-equations": [("quad10", "Nature of roots is the discriminant"),
                                        ("identities9", "Completing the square is (a + b)²"),
                                        ("integers7", "Sums and products of roots need signs right")],
    "mathematics.conic-sections": [("mathematics.straight-lines", "Tangents and normals are lines"),
                                   ("coord10", "Every conic is a distance condition"), ("pythag8", "Distance is Pythagoras")],
    "mathematics.vector-algebra": [("trig10", "Components and the dot product use cos θ"),
                                   ("coords9", "A vector is a point's coordinates, i, j, k"),
                                   ("pythag8", "Magnitude is √(x² + y² + z²)")],
    "mathematics.probability": [("mathematics.permutations-and-combinations", "Counting outcomes is nCr"),
                                ("prob10", "Probability is favourable / total"), ("fractions7", "Multiplying probabilities is multiplying fractions")],
    "mathematics.limits-continuity-and-differentiability": [("mathematics.sets-relations-and-functions", "A limit is about a function"),
                                                            ("slope9", "The derivative is the slope of a curve"),
                                                            ("fractions7", "Limits are fractions simplified")],
    "mathematics.integral-calculus": [("mathematics.limits-continuity-and-differentiability", "Integration is differentiation backwards"),
                                      ("slope9", "Definite integrals are areas under graphs"),
                                      ("area8", "Area under a straight line is a trapezium")],
    # ------------------------------------------------------------------ biology (NEET)
    "biology.molecular-basis-of-inheritance": [("biology.biomolecules", "DNA is a chain of nucleotides"),
                                               ("heredity10", "Genes are what carry traits"),
                                               ("cell9", "DNA sits in chromosomes in the nucleus")],
    "biology.principles-of-inheritance-and-variation": [("heredity10", "Mendel's laws start from dominant and recessive"),
                                                        ("prob10", "Punnett squares are probability"),
                                                        ("fractions7", "Ratios like 9 : 3 : 3 : 1 are fractions")],
    "biology.cell-cycle-and-cell-division": [("biology.cell-the-unit-of-life", "Mitosis moves the organelles and the nucleus"),
                                             ("cell9", "Chromosomes are what divide"), ("reprod9", "Division is how cells copy themselves")],
    "biology.photosynthesis-in-higher-plants": [("reactions10", "The light and dark reactions are redox"),
                                                ("lifeproc10", "Autotrophic nutrition is the Class 10 version"),
                                                ("plants7", "Light, water and CO₂ are the inputs")],
    "biology.breathing-and-exchange-of-gases": [("lifeproc10", "Respiration releases energy using oxygen"),
                                                ("pressure8", "Air enters the lungs from high to low pressure"),
                                                ("animals7", "Breathing in moves the diaphragm down")],
    "biology.human-reproduction": [("reproduce10", "Gametes and fertilisation come from Class 10"),
                                   ("reprod9", "Reproduction keeps a species going"), ("adolescence7", "Puberty hormones start the cycle")],
}


def chain(exam_chapter_id: str, names: dict[str, tuple[str, str, int | None]]) -> list[dict[str, Any]]:
    """A chain in the shape the app stores (gaps.prereq_chain). ``names``: chapter id -> (name, subject, class)."""
    out = []
    for alias, why in CHAINS[exam_chapter_id]:
        link = LINKS[alias]
        name, subject, cls = names[link["chapter_id"]]
        out.append({"chapter_id": link["chapter_id"], "name": name, "subject": subject, "cls": cls,
                    "idea": link["idea"], "why": why, "check": link["check"]})
    return out


def lesson_md(alias: str, target_name: str, why: str) -> str | None:
    body = LINKS[alias].get("lesson")
    if not body:
        return None
    return f"{body}\n\n**How this unlocks {target_name}:** {why}."
