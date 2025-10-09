// Global app state using Svelte 5 runes in a Svelte module

export type MeasurementInfo = {
    name: string;
    description: string;
    measurement_dir: string;
};

export class State {
    // Selected measurement carried between pages
    measurement_choice = $state<MeasurementInfo | null>(null);
}

export const appState = new State();
