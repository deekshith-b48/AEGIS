# Project AEGIS Frontend

A modern, minimalistic frontend for the Project AEGIS Advanced Cybercrime Response System.

## 🎨 Design Philosophy

The UI follows a **minimalistic modern design** approach with:

- **Clean, uncluttered interfaces** with ample whitespace
- **Consistent design system** with thoughtful color usage
- **Smooth animations** and micro-interactions
- **Mobile-first responsive design**
- **Accessibility-first** implementation
- **Data visualization** with clear hierarchy

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for smooth animations
- **Radix UI** for accessible components
- **Recharts** for data visualization
- **Lucide React** for icons

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Building for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Base UI components (Button, Card, Input, etc.)
│   ├── layout/          # Layout components (Navigation, Sidebar)
│   └── charts/          # Chart components
├── pages/               # Page components
│   ├── Dashboard.tsx    # Main dashboard
│   ├── Complaints.tsx   # Complaint management
│   └── Analytics.tsx    # Analytics dashboard
├── lib/                 # Utility functions
├── styles/              # Global styles and CSS
└── App.tsx              # Root component
```

## 🎯 Key Features

### 1. **Dashboard**
- Real-time statistics and metrics
- Interactive data visualizations
- Activity feed and status indicators
- Quick actions and shortcuts

### 2. **Complaint Management**
- Comprehensive complaint listing with filters
- Detailed complaint views
- Status tracking and updates
- Bulk operations

### 3. **Analytics Dashboard**
- Performance metrics and trends
- Data visualization charts
- Geographic hotspots mapping
- AI model performance insights

### 4. **Design System**
- Consistent color palette and typography
- Responsive grid system
- Component variants and states
- Dark mode support (planned)

## 🎨 Design Guidelines

### Color Palette

- **Primary**: Blue (`#3b82f6`)
- **Success**: Green (`#10b981`)
- **Warning**: Yellow (`#f59e0b`)
- **Error**: Red (`#ef4444`)
- **Neutral**: Gray scale with careful contrast ratios

### Typography

- **Font**: Inter (system fallback)
- **Headings**: Bold weights for hierarchy
- **Body**: Regular weights for readability
- **Monospace**: JetBrains Mono for code

### Spacing

- **Base unit**: 4px (0.25rem)
- **Scale**: Consistent 4px grid
- **Containers**: Max-width containers with padding

### Components

- **Cards**: Subtle shadows with hover effects
- **Buttons**: Clear states with transitions
- **Forms**: Accessible inputs with proper labels
- **Navigation**: Clean, organized menu structure

## 📱 Responsive Design

The application is fully responsive with breakpoints:

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px - 1280px
- **Large Desktop**: > 1280px

## 🔧 Customization

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Update navigation in `src/components/layout/Layout.tsx`

### Adding New Components

1. Create component in appropriate `src/components/` directory
2. Follow existing patterns and naming conventions
3. Use TypeScript interfaces for props
4. Include responsive variants

### Theme Customization

1. Update `tailwind.config.js` for colors and spacing
2. Modify `src/styles/globals.css` for custom styles
3. Update design tokens consistently

## 🧪 Testing

```bash
# Run type checking
npm run type-check

# Run linting
npm run lint

# Format code
npm run format
```

## 📊 Data Visualization

The application uses Recharts for data visualization with:

- **Line charts** for trends over time
- **Bar charts** for comparisons
- **Pie charts** for distributions
- **Custom components** for specific use cases

## 🔌 API Integration

The frontend is designed to integrate with the Project AEGIS backend API:

- RESTful API communication
- Real-time WebSocket updates
- Error handling and loading states
- Optimistic updates for better UX

## 🚀 Deployment

### Environment Variables

Create a `.env.production` file:

```env
VITE_API_URL=https://api.aegis.gov.in
VITE_WS_URL=wss://api.aegis.gov.in/ws
VITE_APP_VERSION=2.0.0
```

### Build Process

1. Run `npm run build`
2. Deploy `dist/` folder to your hosting platform
3. Configure server to handle SPA routing

## 🎯 Browser Support

- Chrome/Edge (Latest 2 versions)
- Firefox (Latest 2 versions)
- Safari (Latest 2 versions)
- Mobile browsers (iOS Safari, Android Chrome)

## 🔒 Security

- No sensitive data in frontend
- API communication over HTTPS
- Content Security Policy headers
- Input validation and sanitization

## 📈 Performance

- **Lighthouse Score**: 95+ (Performance, Accessibility, Best Practices, SEO)
- **Bundle Size**: Optimized with code splitting
- **Loading**: Fast initial paint and meaningful content
- **Interactions**: Smooth 60fps animations

## 🤝 Contributing

1. Follow existing code style and patterns
2. Use TypeScript for type safety
3. Write meaningful commit messages
4. Update documentation for changes

## 📝 License

This project is part of Project AEGIS and follows the project's licensing terms.

---

**Note**: This frontend is designed to work seamlessly with the Project AEGIS backend infrastructure. Ensure proper API endpoints are configured before deployment.