import { create } from 'zustand';

export interface TimelineEvent {
  event_type: string;
  payload: any;
}

export interface ReplayState {
  timelineEvents: TimelineEvent[];
  currentIndex: number;
  isPlaying: boolean;
  playbackSpeed: number; // in milliseconds per tick
  reconstructedState: any | null;
  
  setTimelineEvents: (events: TimelineEvent[]) => void;
  setCurrentIndex: (index: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  setReconstructedState: (state: any) => void;
  resetReplay: () => void;
}

export const useReplayStore = create<ReplayState>((set) => ({
  timelineEvents: [],
  currentIndex: -1,
  isPlaying: false,
  playbackSpeed: 1000,
  reconstructedState: null,

  setTimelineEvents: (timelineEvents) => set({ timelineEvents, currentIndex: timelineEvents.length > 0 ? 0 : -1 }),
  setCurrentIndex: (currentIndex) => set({ currentIndex }),
  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setPlaybackSpeed: (playbackSpeed) => set({ playbackSpeed }),
  setReconstructedState: (reconstructedState) => set({ reconstructedState }),
  resetReplay: () => set({ timelineEvents: [], currentIndex: -1, isPlaying: false, reconstructedState: null })
}));
