import type { PageLoad } from './$types';
import { browser } from '$app/environment';

export const load: PageLoad = async ({ fetch }) => {
    if (!browser) {
        // Avoid hitting the backend during prerender/build
        return { meta: { types: [] } };
    }
    const res = await fetch('/api/resources/meta');
    const meta = res.ok ? await res.json() : { types: [] };
    return { meta };
};
