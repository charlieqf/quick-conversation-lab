
import React, { useRef, useEffect } from 'react';

interface Props {
  volume: number; // 0-255
  active: boolean;
  color: string;
}

export const WaveformCanvas: React.FC<Props> = ({ volume, active, color }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  
  // Smoothing
  const currentVol = useRef(0);
  const phaseShift = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // High DPI scaling
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const draw = () => {
      // Lerp for smoothness
      const target = active ? Math.max(volume, 5) : 2; 
      currentVol.current += (target - currentVol.current) * 0.2;
      phaseShift.current += 0.15;

      ctx.clearRect(0, 0, rect.width, rect.height);
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      // Configuration for bars
      const barCount = 5;
      const barWidth = 6;
      const barGap = 6;
      const maxAmplitude = 30; // Max height upwards (and downwards)
      
      const totalWidth = (barCount * barWidth) + ((barCount - 1) * barGap);
      const startX = centerX - (totalWidth / 2);

      for (let i = 0; i < barCount; i++) {
         // Create a wave effect across bars
         const offset = i - (barCount / 2); // -2, -1, 0, 1, 2
         
         // Base height based on volume
         // Add sine wave to make it look "alive" even when volume is low but active
         let barHeight = (currentVol.current / 255) * maxAmplitude * 2;
         
         // Apply a sine wave modification so they don't move in perfect unison
         if (active) {
            const wave = Math.sin(phaseShift.current + (i * 0.8));
            // Combine volume and wave: volume scales the wave intensity
            barHeight = Math.max(4, barHeight * (0.5 + 0.5 * Math.abs(wave)));
            // Center bar is generally taller
            barHeight *= (1 - Math.abs(offset) * 0.2); 
         } else {
             barHeight = 4; // Idle state dot size
         }

         const x = startX + i * (barWidth + barGap);
         const y = centerY - (barHeight / 2);
         
         // Draw rounded rect
         ctx.beginPath();
         ctx.roundRect(x, y, barWidth, barHeight, 20);
         ctx.fillStyle = color;
         ctx.fill();
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [active, color, volume]);

  return <canvas ref={canvasRef} className="w-[120px] h-[60px]" style={{ width: '120px', height: '60px' }} />;
};
