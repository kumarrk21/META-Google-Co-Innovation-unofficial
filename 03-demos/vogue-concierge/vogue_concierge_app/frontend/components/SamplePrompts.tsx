'use client';
import { Sparkles, Package, TrendingUp, Heart, ShieldCheck, Palette } from 'lucide-react';

const PROMPTS = [
  { icon: Heart, label: 'Wedding Guest', text: "I'm attending a summer wedding in Tuscany — what should I wear?" },
  { icon: TrendingUp, label: 'Trending Now', text: 'What are the hottest fashion trends this season?' },
  { icon: Package, label: 'Stock Check', text: 'Check if the Emerald Cocktail Dress is in stock in size 8' },
  { icon: Sparkles, label: 'Style Me', text: 'I need a complete outfit for a business dinner — elegant but modern' },
  { icon: ShieldCheck, label: 'My Rewards', text: 'Do I qualify for a loyalty discount? My customer ID is CUST-1042' },
  { icon: Palette, label: 'Browse', text: 'Show me everything you have in leather accessories' },
];

export default function SamplePrompts({ onSelect }: { onSelect: (text: string) => void }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full px-4">
      {PROMPTS.map((prompt) => {
        const Icon = prompt.icon;
        return (
          <button key={prompt.label} onClick={() => onSelect(prompt.text)}
            className="group flex items-start gap-3 p-3.5 rounded-xl border border-gray-200 bg-white hover:bg-gold-50 hover:border-gold-300 text-left transition-all duration-300 shadow-sm hover:shadow-md">
            <div className="w-8 h-8 rounded-lg bg-gray-50 group-hover:bg-gold-100 flex items-center justify-center flex-shrink-0 transition-colors duration-300">
              <Icon size={14} className="text-gray-400 group-hover:text-gold-600 transition-colors duration-300" />
            </div>
            <div>
              <p className="text-xs font-medium text-gray-700 group-hover:text-gold-700 mb-0.5 transition-colors duration-300">{prompt.label}</p>
              <p className="text-[11px] text-gray-400 leading-snug">{prompt.text}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
