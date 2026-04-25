import { create } from 'zustand';

interface AppState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  activeInstitutionCode: string | null;
  setActiveInstitutionCode: (code: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  activeInstitutionCode: null,
  setActiveInstitutionCode: (code) => set({ activeInstitutionCode: code }),
}));
