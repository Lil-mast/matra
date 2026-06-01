# Frontend Design Docs – Stitch AI Integration

## Overview

This document guides Stitch AI to design the Matra frontend UI/UX. The design should integrate the Matra logo and maintain a modern, accessible, maternal-health-focused aesthetic.

## Logo & Brand Assets

**Logo Location**: `frontend/src/assets/logo.png`

### Brand Guidelines
- **Primary Logo**: Use `logo.png` in the header/navigation bar (responsive sizes: 32px mobile, 48px desktop)
- **Color Scheme**: Derive from the logo – typically warm, approachable colors suitable for maternal health (e.g., soft teals, warm oranges, earth tones)
- **Tone**: Professional yet compassionate – designed for healthcare workers and pregnant women
- **Typography**: Modern, readable sans-serif fonts (e.g., Inter, Poppins, or similar)

## Frontend Architecture

### Tech Stack
- **Framework**: Vanilla TypeScript (No React/Vue/Angular)
- **Build Tool**: Vite 8.0.12
- **Language**: TypeScript ~6.0.2
- **Package Manager**: npm

### Project Structure
```
frontend/
├── index.html           # Entry point
├── package.json         # npm dependencies
├── tsconfig.json        # TypeScript configuration
├── src/
│   ├── main.ts          # App entry (TypeScript)
│   ├── counter.ts       # Sample component logic
│   ├── style.css        # Global styles
│   └── assets/
│       ├── logo.png     # **PRIMARY LOGO** – use in all designs
│       ├── typescript.svg
│       └── vite.svg
└── public/
    ├── favicon.svg
    └── icons.svg
```

## Design Requirements

### 1. **Header/Navigation Bar**
- **Logo Placement**: Top-left, integrated with app title "Matra"
- **Responsive**: Scale logo from 32px (mobile) to 48px (desktop)
- **Navigation Items**: 
  - Dashboard / Home
  - Risk Assessment / Triage
  - Referrals / Reports
  - User Profile / Settings
  - Logout
- **Sticky Header**: Should remain visible on scroll

### 2. **Main Layout**
- **Color Palette**: Derive warm, welcoming tones from logo
- **Grid System**: 12-column responsive grid (mobile-first)
- **Typography**:
  - Headers: Bold, 28-32px (h1), 20-24px (h2)
  - Body: 14-16px, line-height 1.5+
- **Spacing**: 8px base unit (8, 16, 24, 32, 48px increments)

### 3. **Key Pages/Sections**

#### a) **Dashboard (Home)**
- Welcome banner with Matra logo and tagline
- Quick-access cards:
  - "Start Assessment" (primary CTA)
  - "View Recent Referrals"
  - "Sync Offline Data"
  - "View Reports"
- Statistics cards (maternal health metrics)

#### b) **Risk Assessment / Triage Form**
- Multi-step form with progress bar
- Input fields for:
  - Demographics (age, parity)
  - Vital signs (BP, pulse, temperature)
  - Danger signs (checkboxes: bleeding, fever, convulsions, etc.)
- Clear "Submit" and "Cancel" buttons
- Success state with risk level badge (HIGH / INTERMEDIATE / LOW)

#### c) **Referrals / Reports**
- Filterable table or card list
- Patient ID, risk level, date, recommended action
- Badge colors:
  - RED: High Risk
  - ORANGE: Intermediate Risk
  - GREEN: Low Risk

#### d) **User Profile**
- Profile picture placeholder
- User role (CHW, Hospital, Manager)
- Clinic name / location
- Settings toggle (language, notifications, theme)

### 4. **Visual Design Elements**

#### Colors
- **Primary**: Derive from logo (warm accent color)
- **Secondary**: Complementary tone (calm, trustworthy)
- **Success**: Green (#10B981)
- **Warning**: Orange (#F59E0B)
- **Danger**: Red (#EF4444)
- **Neutral**: Gray scale (#1F2937 → #F9FAFB)

#### Buttons
- **Primary Button**: Full logo color, white text, 8px border-radius, 12px padding
- **Secondary Button**: Outlined, gray text
- **Disabled State**: Opacity 50%, cursor not-allowed

#### Cards
- **Elevation**: Subtle shadow (0 1px 3px rgba(0,0,0,0.1))
- **Padding**: 16-20px
- **Border-radius**: 8px

#### Forms
- **Input Fields**: Border-bottom style or subtle border, focus: primary color underline
- **Labels**: Bold, 12px, margin-bottom 4px
- **Error State**: Red border, error message below

### 5. **Accessibility (WCAG 2.1 AA)**
- **Contrast Ratio**: Minimum 4.5:1 for text
- **Focus Indicators**: Visible keyboard focus on all interactive elements
- **Alt Text**: Logo and all images must have descriptive alt text
- **ARIA Labels**: Form fields, buttons, regions
- **Keyboard Navigation**: Tab order logical, escape to close modals
- **Mobile Touch**: Tap targets minimum 44×44px

### 6. **Responsive Breakpoints**
- **Mobile**: 320px – 768px (single column, stacked navigation)
- **Tablet**: 768px – 1024px (two-column, hamburger nav collapsible)
- **Desktop**: 1024px+ (three-column, full navigation)

### 7. **Interactive States**
- **Hover**: Subtle color shift, cursor pointer on clickables
- **Active**: Underline or highlight for current page
- **Loading**: Spinner or skeleton loader
- **Success**: Checkmark animation, toast notification
- **Error**: Shake animation, inline error message

## Design File Handoff

### For Stitch AI
1. **Create wireframes** with logo placement in header
2. **Design high-fidelity mockups** for:
   - Desktop view (1440px)
   - Tablet view (768px)
   - Mobile view (375px)
3. **Color Palette Export**: CSS variables for all brand colors
4. **Component Library**: 
   - Buttons (primary, secondary, danger, disabled)
   - Input fields
   - Cards
   - Badges (risk levels)
   - Navigation bar
   - Modals
5. **Typography Spec**: Font family, sizes, weights, line heights
6. **Spacing Guide**: 8px grid system

## Frontend Development Notes

- Use CSS variables for all colors (derived from Stitch AI design)
- Implement mobile-first responsive design
- Ensure all interactive elements have keyboard focus states
- Use `<picture>` tag for logo with responsive sizes
- Lazy load images where applicable

## Next Steps for Engineering

1. **Export Design Assets**: SVG icons, logo variations (light/dark)
2. **Create CSS Framework**: Based on Stitch AI palette and typography
3. **Implement Components**: Vanilla TypeScript + CSS
4. **Test Accessibility**: axe-core, WAVE, manual keyboard testing
5. **Deploy**: Build via `npm run build`, preview with `npm run preview`

---

**Design Tool**: Stitch AI  
**Package Manager**: npm  
**Build Tool**: Vite  
**Primary Asset**: `frontend/src/assets/logo.png`
