import React, { useState } from 'react';
import { APIVoice } from '../../../types';
import { Mic, Play, Volume2, Loader2, VolumeX } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';

interface VoiceSelectorProps {
  selectedVoice: string;
  modelId: string;
  onSelect: (id: string) => void;
  voices: APIVoice[];
  isLoading?: boolean;
}

export const VoiceSelector: React.FC<VoiceSelectorProps> = ({ selectedVoice, modelId, onSelect, voices, isLoading }) => {
  const { token } = useAuth();
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);

  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const playPreview = async (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (playingVoiceId) return; // Prevent multiple plays

    try {
      setPlayingVoiceId(voiceId);
      setIsPlaying(true);

      const res = await fetch('/api/models/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          modelId: modelId,
          voiceId: voiceId,
          text: "Hello! This is a preview of my voice."
        }),
      });

      if (!res.ok) {
        if (res.status === 501) {
          alert("Preview not available for this model yet.");
        } else {
          throw new Error("Preview failed");
        }
        return;
      }

      const blob = await res.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audio.onended = () => {
        setPlayingVoiceId(null);
        setIsPlaying(false);
      };
      await audio.play();

    } catch (err) {
      console.error(err);
      alert("Failed to play preview");
      setPlayingVoiceId(null);
      setIsPlaying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mb-6 animate-pulse text-slate-400 text-sm">
        Loading voices...
      </div>
    );
  }

  if (voices.length === 0) {
    return (
      <div className="mb-6 p-4 bg-slate-50 border border-slate-200 rounded-lg text-center text-slate-500 text-sm">
        <p>No voices available for the selected model.</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
        <Mic className="w-4 h-4 mr-2 text-medical-600" />
        语音声线 (Voice)
      </h3>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 divide-y divide-slate-50">
        {voices.map((voice) => {
          const isSelected = selectedVoice === voice.id;
          const isPlaying = playingVoiceId === voice.id;

          return (
            <div
              key={voice.id}
              onClick={() => onSelect(voice.id)}
              className={`
                flex items-center justify-between p-3 cursor-pointer transition-colors
                ${isSelected ? 'bg-medical-50/20' : 'hover:bg-slate-50'}
              `}
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-lg">
                  {/* Use icon if available, else default */}
                  {voice.icon || (voice.gender === 'Male' ? '👨' : '👩')}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${isSelected ? 'text-medical-700' : 'text-slate-700'}`}>
                      {voice.name}
                    </span>
                    <span className={`
                      text-[10px] px-1.5 py-0.5 rounded border
                      ${voice.gender === 'Male'
                        ? 'bg-blue-50 text-blue-600 border-blue-100'
                        : 'bg-rose-50 text-rose-600 border-rose-100'}
                    `}>
                      {voice.gender === 'Male' ? '男声' : '女声'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    {voice.style || 'Standard Voice'}
                  </p>
                </div>
              </div>

              {/* Play Sample Button */}
              <button
                onClick={(e) => playPreview(voice.id, e)}
                disabled={isPlaying && playingVoiceId !== voice.id}
                className={`
                  w-8 h-8 flex items-center justify-center rounded-full transition-all
                  ${isPlaying && playingVoiceId === voice.id
                    ? 'text-medical-600 bg-medical-50 animate-pulse'
                    : 'text-slate-300 hover:text-medical-600 hover:bg-slate-100'}
                `}
                title="点击试听 (Preview Voice)"
              >
                {isPlaying && playingVoiceId === voice.id ? (
                  <Volume2 className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4 ml-0.5" />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};