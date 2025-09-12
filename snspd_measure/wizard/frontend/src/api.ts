export function fetchWithConfig<T = any>(
    url: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    body?: Record<string, any> | null
): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const controller = new AbortController();
    const signal = controller.signal;

    const config: RequestInit = {
        method,
        signal,
        headers
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    const result_promise = fetch(url, config)
        .then((response: Response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json() as Promise<T>;
        })
        .catch((error: unknown) => {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            console.error('Fetch error:', error);
            throw new Error(`Failed to fetch: ${errorMessage}`);
        });

    return result_promise;
}
