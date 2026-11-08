---
name: ai-product-designer
description: |
  Full product development workflow for business/commercial product conceptualization.
  Use for business product development: design a product line, develop a new product for a market/audience, create a product strategy, or produce multiple differentiated product design options.
  Use for market-driven design: design based on trends, analyze market context and design, or decide what products to develop for a target audience.
  Use for end-to-end development: from concept to suppliers, design to market, finding suppliers for a product idea, or comparing supplier capabilities for proposed concepts.
  Applicable categories: apparel and clothing, footwear and bags, jewelry and accessories, home and living, consumer gifts and souvenirs, beauty and personal care, electronics and digital accessories, baby and kids, pet supplies, sports and outdoor.
  Do not use for simple one-off image generation, logos/branding/posters, food and beverages, books/media, virtual goods/services, industrial equipment/parts, pure sourcing for existing products, or inquiry/order flows.
---

# New Product Development & Design

A comprehensive workflow for end-to-end product conceptualization: from market analysis to design proposals to supplier matching.

## Core Principles

1. **Demand First**: Always restate user goals & constraints before proceeding
2. **Visuals When Needed**: When the buyer asks for visual design output or proposal renders, create real images with the available Phoenix image tool; otherwise provide structured concepts without inventing image URLs
3. **Differentiation**: Generate the requested number of distinct proposals; default to 3 when the buyer does not specify a quantity
4. **Visual Consistency**: When images are generated, every proposal must have one comparable hero product image
5. **Complete Analysis**: Each proposal MUST include Positioning & Value paragraph + Key Specs table
6. **Per-Proposal Analysis**: Evaluate each proposal individually, especially for sourcing
7. **Actionability**: End with clear recommendations and phased action plan

---

## How to Use

Read this guide when the buyer wants a product concept, product line, or differentiated proposal set rather than a simple search for existing listings.

## Phoenix Adaptation

This is a business workflow skill, not a tool manual. Use Phoenix tools only when the current step requires images, market evidence, or supplier data.

- For new product concept renders, use the Phoenix image generation tool. In Phoenix this is `image_generate`; pass a complete product-image brief as `prompt`, and use `task_type: "complex"` for multi-constraint concept renders.
- For edits to a buyer-provided or previously generated product image, use `image_edit` with `reference_images`. Do not use old sandbox parameter names such as `reference_image_list`.
- For current market context, use lightweight search/fetch only when evidence can change the design direction.
- If the buyer asks for suppliers, manufacturers, factories, or Alibaba.com listings, treat sourcing as a later step after concepts are clear; then read `accio-product-supplier-sourcing`.
- Do not rely on legacy sandbox-only paths, helper scripts, or unavailable old-agent tools.

---

## Steps

### Step 1: Demand Understanding
- **Input**: User query
- **Action**: Restate goals, constraints, and product category
- **Output**: Confirmed interpretation of user needs

### Step 2: Market Analysis & Strategy (Search-first by Default)
- **Input**: Any product development request where market context could change the recommendation (this includes requests with detailed specs).
- **Skip only if (must be explicit in user query)**:
  - User explicitly requests **no external search / no market research**, OR
  - User explicitly states they already have **validated market data** and only want **execution/design output**.
- **Action**:
  - Use `web_search` for broad current market signals and `web_fetch` only for the most relevant sources that need verification.
  - Keep research proportional: gather enough context to support the design direction, not a full market report unless requested.
  - Check at least two source types when practical, such as marketplace listings, consumer reviews, brand/product pages, trend articles, or social/community signals.
  - Stop once you can justify 3 design strategies and identify the main user pain points, competitive gaps, and production risks.
- **Output**:
  - Feasibility verdict (Yes / Cautious / No + "Why now?")
  - Trend trajectory (seasonality, sales peaks)
  - Consumer pain points (from negative review analysis)
  - Competitive gaps (category opportunities)
  - **Design Strategies** (Output exactly 3; each must be evidence-backed):
    ```
    Strategy [N]: [Title]
    - Core Concept: [Direction, e.g., "Eco-Minimalism"]
    - Reason and Evidence: [Why this strategy works and supporting data/case]
    ```

### Step 3: Design Proposals
- **Input**: User needs + market insights
- **Action**: Generate the buyer-requested number of differentiated proposals. If no quantity is specified, generate 3 distinct proposals (Entry-level / Premium / Innovative).
- **Output**: Per proposal (structured format):
  1. **Title**: Proposal X: [Memorable Theme Name] — Create a catchy, evocative title (e.g., "Proposal 1: Urban Stealth Fortress", "Proposal 2: Nomad Life Essential")
  2. **Positioning & Value**: Three concise points (1-2 sentences each):
     - **Positioning**: [Target user] + [Product positioning] — e.g., "A minimalist storage tool for students"
     - **User Value**: [Design approach] + [Specific pain point solved] — what design solves what problem
     - **Business Value**: [Commercial opportunity: volume driver/hero/entry SKU] + [Production risks/barriers]
  3. **Visual**: One hero product image
     - If the buyer requested visual output or proposal renders, call the available image generation tool; in Phoenix this is `image_generate`
     - Use comparable white-background product images for all proposals when visuals are generated
     - If the buyer only wants strategy, specs, or sourcing logic, describe the intended hero visual but do not fabricate image URLs
  4. **Key Specs**: Table format with **at least 5 relevant fields**, adapted by product category:
     | Category | Recommended Fields |
     |----------|-------------------|
     | Apparel | Materials, Size Range, Fit/Silhouette, Craft/Details, Target Cost, MOQ |
     | Bags/Gear | Materials, Dimensions, Structure/Compartments, Hardware, Craft, Target Cost |
     | Electronics | Core Features, Specs/Parameters, Materials, Certifications, Target Cost, MOQ |
     | Furniture | Materials, Dimensions, Load Capacity, Assembly, Craft, Target Cost |
     | Beauty | Key Ingredients, Capacity, Packaging, Certifications, Target Cost, Shelf Life |

### Step 4: Proposal Comparison
- **Input**: Completed proposals
- **Action**: Compare across dimensions, recommend winner
- **Output**: 
  - **Comparison Table**: Positioning, Key Differentiator, Material/Craft, Cost Range, Time to Market, Advantages (2-3 pts), Risks (2-3 pts), Strategic Role
  - **Primary Recommendation**: Core Winning Point + vs Proposal A/B + Strategic Fit
  - **Alternative**: Best if [different priority]

### Step 5: Sourcing & Supplier Matching (Optional)
- **Input**: User requests suppliers ("Find manufacturers", "Who can make this?")
- **Action**:
  - First, ask the buyer which proposal(s) they want to source unless they already selected one.
  - Then read `accio-product-supplier-sourcing` before using `product_supplier_search`.
  - Analyze sourcing for EACH selected proposal separately.
- **Output**: For EACH proposal:
  - Required Capabilities (specific factory type for THIS proposal)
  - Certifications (based on THIS proposal's needs)
  - MOQ Compatibility
  - Recommended Suppliers (1-2 suited for THIS specific proposal)
  - Key Inquiry Points & Negotiation Focus
- **Cross-Proposal Comparison**: Supplier Type, Lead Time, MOQ, Best For
- **Final Recommendation**: Which sourcing path offers best balance
- **Prompt at end**: "Would you like me to find suppliers for any of these designs?"

### Step 6: Next Step (as follow-up chips)
- **Input**: All proposals presented
- **Action**: Offer 3-4 next steps the buyer can choose from
- **Output**: emit them as follow-up chips using `<follow>...</follow>` tags per the Follow-up Output Rules — **not** a numbered list or a `### Next Step` heading.
  - Render all chip text in the buyer's language.
  - Concatenate chip tags with no whitespace between them. Each payload is a **buyer-voice** actionable request (≤ ~12 words), with no `<`, `>`, or `&`.
  - Optional one-line intro prose before the chips (e.g. "To move this project forward:").
  - Cover specific actions: refine a proposal's details, explore more variations, match suppliers, create an execution plan.
  - Example:
    ```
    To move this project forward:

    <follow>Refine Proposal 2's structure and build a detailed BOM</follow><follow>Generate more differentiated design directions</follow><follow>Find and screen suppliers for Proposal 1</follow><follow>Create an execution plan from tooling to first batch</follow>
    ```

---

## Output Format

### Proposal Structure

```
### Proposal [N]: [Memorable Theme Name]

**Positioning & Value**

1. **Positioning**: [Target user + product positioning in one sentence]
2. **User Value**: [Design approach + specific pain point solved]
3. **Business Value**: [Commercial opportunity + production risks/barriers]

**Hero Visual**

Here is the hero product image for this proposal:

[generated hero product image appears here when visual output is requested]

**Key Specs**

| Field | Content |
|-------|---------|
| Materials | [Primary materials with grades/specs] |
| Dimensions | [Size/capacity appropriate to product] |
| Core Features | [Key features, differentiators] |
| Structure | [Components, compartments, assembly] |
| Craft/Details | [Craft techniques, finishing, QC points] |
| Target Cost | BOM $[X-Y] / Retail $[X-Y] |
| MOQ/Lead Time | [Minimum order quantity, production timeline] |
```

**Note**: Include **at least 5 fields** from the following, adapted by product category:
- Apparel: Materials, Size Range, Fit/Silhouette, Craft/Details, Target Cost, MOQ
- Bags/Gear: Materials, Dimensions, Structure/Compartments, Hardware, Craft, Target Cost
- Electronics: Core Features, Specs/Parameters, Materials, Certifications, Target Cost
- Furniture: Materials, Dimensions, Load Capacity, Assembly, Craft, Target Cost
- Beauty: Key Ingredients, Capacity, Packaging, Certifications, Target Cost, Shelf Life

### Comparison Table

| Dimension | Proposal 1 | Proposal 2 | Proposal N |
|-----------|------------|------------|------------|
| Positioning | ... | ... | ... |
| Key Differentiator | ... | ... | ... |
| Material/Craft | ... | ... | ... |
| Cost Range | $X-Y | $X-Y | $X-Y |
| Time to Market | X weeks | ... | ... |
| Advantages | 2-3 pts | 2-3 pts | 2-3 pts |
| Risks | 2-3 pts | 2-3 pts | 2-3 pts |
| Strategic Role | Hero/Cash-cow/Test | ... | ... |

### Recommendation

**Primary Pick**: [Proposal Name]

| Element | Content |
|---------|---------|
| **Core Winning Point** | The unique "killer feature" (1 sentence) |
| **vs Proposal A** | Why this beats A on [specific dimension] |
| **vs Proposal B** | Why this beats B on [specific dimension] |
| **Strategic Fit** | Why this aligns with brand's goals |

**Alternative**: [Proposal Name] — Best if [different priority]

Next steps — emit as buyer-voice follow-up chips using contiguous `<follow>...</follow>` tags with no whitespace between them (no numbered list or `### Next Step` heading):

To move this project forward:

<follow>Refine a proposal's structure and build a detailed BOM</follow><follow>Generate more differentiated design directions</follow><follow>Find and screen suppliers for my chosen proposal</follow><follow>Create an execution plan from tooling to first batch</follow>

---

## Checklist

**Must Have**:
- [ ] Demand restatement
- [ ] Requested number of distinct proposals; default 3 when unspecified (differentiated positioning, not just color swaps)
- [ ] **Memorable title per proposal** (Proposal X: [Theme Name], catchy and evocative)
- [ ] **Positioning & Value in 3 points**: (1) Positioning, (2) User Value, (3) Business Value — each 1-2 sentences
- [ ] **Generated product image per proposal when visual output is requested** (call the image tool; do not use placeholder text)
- [ ] **Key Specs table with at least 5 fields** (adapted by product category)
- [ ] Comparison table + primary recommendation
- [ ] **Next-step options emitted as 3-4 buyer-voice `<follow>...</follow>` tags** (never a numbered list or `### Next Step` heading)

**Conditional**:
- [ ] Market Analysis (search-first by default; only skip if user explicitly waives external search/market research)
- [ ] Sourcing - per proposal separately (when user requests)

**Avoid**:
- Promising generated images without calling an image tool or providing real displayed results
- **Positioning & Value as long paragraph** (use 3-point structure instead)
- **Missing any of the 3 value points** (Positioning, User Value, Business Value — all required)
- **Key Specs table with fewer than 5 fields** (adapt fields to product category, but always at least 5)
- **Mixing languages** (e.g., English headers with Chinese content, or vice versa — pick ONE language and stick to it)
- **Complex phased action plans** (use simple next-step follow-up chips instead)
- Vague "all proposals are good" (must have clear winner)
- Bulk sourcing analysis (analyze separately)
- Over-engineering simple products

---

## Example

### Wrong Example (What NOT to do):

```
Proposal 1: Basic Ceramic Mug

**Value**:
- Target: Young professionals
- Positioning: Entry-level
- User Value: Comfortable morning ritual
- Business Value: Low cost, high margin

Visual Assets:
- White BG Product: [Conceptualizing: A minimalist ceramic mug]
```
**Problems**: 
- Title not memorable (should be like "Proposal 1: Morning Comfort Ritual")
- Positioning & Value uses bullet points instead of flowing prose
- No actual image generated
- Missing Key Specs table

---

### Correct Example (What TO do):

```
### Proposal 1: Nomad Life Essential — Urban Stealth Gear

**Positioning & Value**

1. **Positioning**: A minimalist anti-theft backpack for students and young commuters in crowded urban environments.
2. **User Value**: Charcoal-black color scheme with hidden-compartment design creates "visual stealth," solving security anxiety and belongings protection during daily commutes.
3. **Business Value**: Simple craft with standard materials, ideal as a volume-driving SKU for quick market capture; low production barriers but thin margins due to competitive pricing.

**Hero Visual**

[generated hero product image appears here when visual output is requested]

**Key Specs**

| Field | Content |
|-------|---------|
| Materials | 600D recycled polyester + PU waterproof coating |
| Dimensions | 45×30×15cm (25L capacity) |
| Structure | Main compartment + hidden back panel pocket + side mesh pockets |
| Core Features | Hidden back-panel zipper, RFID passport sleeve, quick-release strap buckle, reflective safety strip |
| Hardware | YBS zippers, adjustable chest strap with whistle buckle |
| Craft/Details | Reinforced stitching at stress points + heat-sealed inner seams for water resistance |
| Target Cost | BOM $12-18 / Retail $49-59 |
| MOQ/Lead Time | MOQ 500pcs / Lead time 25-30 days |

[Repeat the same structure for every requested proposal]

---

Next steps as buyer-voice follow-up chips (no numbered list, no `### Next Step` heading):

To move this project forward:

<follow>Refine a proposal's structure and build a detailed BOM</follow><follow>Generate more differentiated design directions</follow><follow>Find and screen suppliers for my chosen proposal</follow><follow>Create an execution plan from tooling to first batch</follow>
```
**Correct**: 
- Memorable title (Nomad Life Essential — Urban Stealth Gear)
- **3-point Positioning & Value** structure (concise, 1-2 sentences each)
- Actual generated image
- Key Specs table with **8 fields** (minimum 5 required)
- Next-step options emitted as buyer-voice `<follow>...</follow>` tags
