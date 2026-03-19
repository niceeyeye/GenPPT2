import { useEffect, useRef } from 'react';
import Reveal from 'reveal.js';
import 'reveal.js/reveal.css';

interface SlideItem {
  title: string;
  description: string;
}

interface Slide {
  page_title: string;
  subtitle?: string;
  content: SlideItem[];
  layout_type: string;
  image_description?: string;
}

interface PreviewProps {
  slides: Slide[];
  title: string;
  subtitle?: string;
  themeColor?: string;
  accentColor?: string;
  bgStyle?: string;
}

export function Preview({ slides, title, subtitle, themeColor = "#4F46E5", accentColor = "#06B6D4", bgStyle = "gradient" }: PreviewProps) {
  const deckRef = useRef<HTMLDivElement>(null);
  const revealInstance = useRef<any>(null);

  useEffect(() => {
    // Adding a small timeout to ensure DOM is fully rendered before Reveal.js calculation
    const timer = setTimeout(() => {
      if (deckRef.current) {
        if (revealInstance.current) {
          revealInstance.current.destroy();
          revealInstance.current = null;
        }
        
        revealInstance.current = new Reveal(deckRef.current, {
          embedded: true,
          controls: true,
          progress: true,
          center: false,
          width: 1280,
          height: 720,
          margin: 0.05,
          minScale: 0.2,
          maxScale: 2.0,
          hash: false,
          transition: 'slide',
          backgroundTransition: 'slide',
          mouseWheel: true,
          display: 'flex',
          keyboard: true,
          disableLayout: false
        });
        
        revealInstance.current.initialize().then(() => {
           revealInstance.current?.layout(); // Force a layout recalculation
        }).catch((err: any) => {
          console.error("Reveal.js initialization error:", err);
        });
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      if (revealInstance.current) {
        try {
          revealInstance.current.destroy();
        } catch (e) {}
        revealInstance.current = null;
      }
    };
  }, [slides, title]);

  if (!Array.isArray(slides)) {
    return <div className="p-8 text-center text-red-500 bg-red-50 rounded-lg">Invalid slides data structure</div>;
  }

  const getBgStyle = () => {
    if (bgStyle === 'gradient') return { background: `linear-gradient(135deg, ${themeColor} 0%, ${accentColor} 100%)` };
    if (bgStyle === 'mesh') return { 
      backgroundColor: themeColor,
      backgroundImage: `radial-gradient(at 40% 20%, ${accentColor} 0px, transparent 50%), radial-gradient(at 80% 0%, ${themeColor} 0px, transparent 50%), radial-gradient(at 0% 50%, ${themeColor} 0px, transparent 50%)`
    };
    return { backgroundColor: themeColor };
  };

  return (
    <div className="reveal font-sans" ref={deckRef} style={{ height: '500px', width: '100%', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.1)' }}>
      <style>{`
        /* Animations for Preview */
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInRight {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes widthGrow {
          from { width: 0; }
          to { width: 80px; }
        }

        /* Only animate when the slide is present (active) */
        .reveal .slides section.present .animate-fade-up {
          animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .reveal .slides section.present .animate-fade-right {
          animation: fadeInRight 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .reveal .slides section.present .animate-scale {
          animation: scaleIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .reveal .slides section.present .animate-width {
          animation: widthGrow 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        /* Staggered delays for cards */
        .reveal .slides section.present .vibe-card:nth-child(1) { animation-delay: 0.1s; }
        .reveal .slides section.present .vibe-card:nth-child(2) { animation-delay: 0.2s; }
        .reveal .slides section.present .vibe-card:nth-child(3) { animation-delay: 0.3s; }
        .reveal .slides section.present .vibe-card:nth-child(4) { animation-delay: 0.4s; }

        /* Initial state for animated elements */
        .animate-fade-up, .animate-fade-right, .animate-scale, .vibe-card {
          opacity: 0;
        }
      `}</style>
      <div className="slides">
        {/* Title Slide */}
        <section style={{ ...getBgStyle(), color: '#fff', position: 'relative' }} className="h-full w-full flex flex-col justify-center px-24 text-left">
          <div className="absolute inset-0 bg-black/20 z-0"></div>
          <div className="relative z-10">
            <h2 className="animate-fade-up text-6xl font-extrabold mb-6 tracking-tight leading-tight text-white drop-shadow-lg" style={{ textShadow: '0 10px 30px rgba(0,0,0,0.3)' }}>
              {title || "Untitled PPT"}
            </h2>
            {subtitle && <p className="animate-fade-up text-2xl text-white/90 mb-10 font-light" style={{ animationDelay: '0.2s' }}>{subtitle}</p>}
            <div className="animate-width" style={{ width: '80px', height: '6px', backgroundColor: accentColor, borderRadius: '3px', boxShadow: `0 0 20px ${accentColor}`, animationDelay: '0.4s' }}></div>
            <p className="animate-fade-up mt-16 text-sm text-white/50 font-mono tracking-widest uppercase" style={{ animationDelay: '0.6s' }}>GENERATED BY GENPPT VIBE AI</p>
          </div>
        </section>
        
        {slides.map((slide, index) => {
          const l_type = (slide.layout_type || '').toLowerCase().replace(/-/g, '_').replace(/ /g, '_');
          // Important fix: check if content array is genuinely empty or undefined
          const isTitleOnly = l_type.includes('title') || l_type === 'cover' || !slide.content || slide.content.length === 0 || (slide.content.length === 1 && !slide.content[0].title && !slide.content[0].description);
          const isTwoColumns = l_type.includes('two') || l_type.includes('column');
          const isTimeline = l_type.includes('time') || l_type.includes('step');
          
          if (isTitleOnly) {
            return (
              <section key={`slide-${index}`} style={getBgStyle()} className="h-full w-full flex flex-col justify-center items-center text-center px-12">
                <h2 className="animate-scale text-5xl font-extrabold text-white leading-tight drop-shadow-lg">{slide.page_title}</h2>
                {slide.subtitle && <p className="animate-fade-up text-2xl text-white/80 mt-8" style={{ animationDelay: '0.3s' }}>{slide.subtitle}</p>}
              </section>
            );
          }
          
          return (
            <section key={`slide-${index}`} className="text-left px-16 h-full w-full flex flex-col justify-start pt-16 pb-12 bg-gradient-to-tr from-white to-slate-50">
              {/* Header */}
              <div className="mb-10">
                <h3 className="animate-fade-right text-4xl font-extrabold mb-2 tracking-tight" style={{ color: themeColor }}>
                  {slide.page_title}
                </h3>
                {slide.subtitle && <p className="animate-fade-right text-slate-500 text-lg font-medium" style={{ animationDelay: '0.2s' }}>{slide.subtitle}</p>}
                <div className="animate-width w-16 h-1 mt-6 rounded-full" style={{ backgroundColor: accentColor, animationDelay: '0.4s' }}></div>
              </div>
              
              {/* Content Area */}
              <div className="flex-1 flex flex-col justify-start overflow-hidden">
                
                {isTwoColumns ? (
                  <div className="flex flex-col gap-4 overflow-y-auto pr-2">
                    {slide.content.map((item, idx) => (
                      <div key={idx} className="vibe-card animate-fade-up bg-white p-6 rounded-2xl shadow-sm border-l-4" style={{ borderColor: themeColor }}>
                        <h4 className="text-slate-900 font-bold text-xl mb-2">{item.title}</h4>
                        <p className="text-slate-600 text-sm leading-relaxed">{item.description}</p>
                      </div>
                    ))}
                  </div>
                ) : isTimeline ? (
                  <div className="flex flex-col gap-4 overflow-y-auto pl-2 py-2">
                    {slide.content.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-6">
                        <div className="animate-scale flex flex-col items-center mt-1" style={{ animationDelay: `${0.5 + idx * 0.1}s` }}>
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-md" style={{ backgroundColor: accentColor, boxShadow: `0 0 15px ${accentColor}66` }}>
                            {idx + 1}
                          </div>
                          {idx < slide.content.length - 1 && (
                            <div className="w-0.5 h-12 mt-2 bg-gradient-to-b" style={{ backgroundImage: `linear-gradient(to bottom, ${accentColor}, transparent)` }}></div>
                          )}
                        </div>
                        <div className="vibe-card animate-fade-right flex-1 bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow" style={{ animationDelay: `${0.6 + idx * 0.1}s` }}>
                          <h4 className="font-bold text-lg mb-1" style={{ color: themeColor }}>{item.title}</h4>
                          <p className="text-slate-600 text-sm leading-relaxed">{item.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  /* Cards Layout */
                  <div className={`grid gap-6 overflow-y-auto p-2 ${slide.content.length <= 4 ? 'grid-cols-2' : 'grid-cols-3'}`}>
                    {slide.content.map((item, idx) => (
                      <div key={idx} className="vibe-card animate-fade-up bg-white p-6 rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.03)] border-t-4 flex flex-col hover:-translate-y-1 transition-transform duration-300" style={{ borderColor: accentColor }}>
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ backgroundColor: `${themeColor}15` }}>
                          <div className="w-4 h-4 rounded-sm" style={{ backgroundColor: themeColor }}></div>
                        </div>
                        <h4 className="text-slate-900 font-bold text-xl mb-3">{item.title}</h4>
                        <p className="text-slate-500 text-sm leading-relaxed flex-1">{item.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
