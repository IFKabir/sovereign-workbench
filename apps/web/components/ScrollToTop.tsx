'use client';

import { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const toggleVisible = () => {
      if (window.scrollY > 200 || document.documentElement.scrollTop > 200) {
        setVisible(true);
      } else {
        setVisible(false);
      }
    };
    window.addEventListener('scroll', toggleVisible, { passive: true });
    return () => window.removeEventListener('scroll', toggleVisible);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  if (!visible) return null;

  return (
    <button
      onClick={scrollToTop}
      className="fixed bottom-6 right-6 z-50 p-3 bg-[#8fb03e] text-[#1a1a1a] border border-white font-bold shadow-xl hover:bg-[#57692c] hover:text-white transition-all flex items-center justify-center select-none cursor-pointer"
      title="Scroll to Top / ऊपर जाएं"
    >
      <ArrowUp className="w-5 h-5 stroke-[3]" />
    </button>
  );
}
