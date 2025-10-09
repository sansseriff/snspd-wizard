import { browser } from '$app/environment';
import { fetchWithConfig } from '../../api';

export const load = async ({ fetch, url }: any) => {
    // Ensure this only runs in the browser so the state module is available
    if (!browser) {
        return { measurementName: null, instruments: [] as string[] };
    }

    const name = url.searchParams.get('name');
    if (!name) {
        return { measurementName: null, instruments: [] as string[] };
    }

    let instruments = await fetchWithConfig(`/api/get-instruments/${encodeURIComponent(name)}`, 'GET');
    instruments = Array.isArray(instruments) ? instruments : [];

    return { measurementName: name, instruments };
};

export const prerender = true;
export const ssr = false;
