<script lang="ts">
	import { ScrollArea } from 'bits-ui';
	import { goto } from '$app/navigation';

	// Types matching the backend payload
	type MatchingReq = {
		module: string;
		class_name: string;
		qualname?: string;
		friendly_name?: string;
		file_path?: string;
	};

	type OutputReq = {
		variable_name: string;
		base_type: string; // e.g. "<class 'instruments.general.vsource.VSource'>"
		matching_instruments: MatchingReq[];
	};

	let { data } = $props();
	const measurementName: string | null = data?.measurementName ?? null;
	const reqs: OutputReq[] = (data?.instruments ?? []) as OutputReq[];

	// Track selection per requirement (keyed by variable_name -> qualname/module+class)
	const selected: Record<string, string | null> = $state({});
	for (const r of reqs) {
		if (!(r.variable_name in selected)) selected[r.variable_name] = null;
	}
	const allSelected = $derived(
		Boolean(reqs.length && reqs.every((r) => selected[r.variable_name]))
	);

	function shortBaseName(bt: string): string {
		const m = bt?.match(/<class '([^']+)'>/);
		const full = m?.[1] ?? bt ?? '';
		const parts = full.split('.');
		return parts[parts.length - 1] || full;
	}

	function fullBaseModule(bt: string): string {
		const m = bt?.match(/<class '([^']+)'>/);
		return m?.[1] ?? bt ?? '';
	}

	function displayName(m: MatchingReq): string {
		return m.friendly_name || m.class_name || 'Unknown';
	}

	function displaySub(m: MatchingReq): string {
		const mod = m.module ? `${m.module}.${m.class_name}` : m.class_name;
		return mod ?? '';
	}

	function selectReq(r: OutputReq, m: MatchingReq) {
		const key = m.qualname || (m.module ? `${m.module}.${m.class_name}` : m.class_name);
		selected[r.variable_name] = key ?? null;
	}

	function onNext() {
		// Placeholder for next step; wire to your flow as needed
		goto('/');
	}
</script>

<section class="space-y-4">
	<h1 class="text-2xl font-semibold">Select instruments</h1>
	{#if !measurementName}
		<div class="text-sm text-gray-600 dark:text-gray-300">
			No measurement selected. <a class="text-indigo-600 underline" href="/get_measurements"
				>Go back</a
			>.
		</div>
	{:else}
		<p class="text-sm text-gray-600 dark:text-gray-300">
			Measurement: <span class="font-medium">{measurementName}</span>
		</p>
	{/if}

	{#if measurementName}
		{#if !reqs || reqs.length === 0}
			<div
				class="rounded-xl border border-gray-200 bg-white/70 p-4 text-sm text-gray-600 dark:border-white/10 dark:bg-gray-800/70 dark:text-gray-300"
			>
				No instrument roles detected for this measurement.
			</div>
		{:else}
			<div class="space-y-8">
				{#each reqs as r}
					<section class="space-y-2">
						<h2 class="text-lg font-medium">required: {r.variable_name}</h2>
						<p class="text-xs text-gray-600 dark:text-gray-300">
							Instruments that implement the {shortBaseName(r.base_type)} API
							<span class="text-[10px] text-gray-500 dark:text-gray-400"
								>({fullBaseModule(r.base_type)})</span
							>
						</p>

						<ScrollArea.Root
							class="relative overflow-hidden rounded-xl border border-gray-200 bg-white/70 p-3 shadow-sm dark:border-white/10 dark:bg-gray-800/70"
						>
							<ScrollArea.Viewport class="h-full max-h-[260px] w-full">
								{#if r.matching_instruments?.length}
									<ul class="divide-y divide-gray-200 dark:divide-white/10">
										{#each r.matching_instruments as m}
											<li>
												<button
													class={`w-full rounded-md px-3 py-3 text-left transition ${selected[r.variable_name] === (m.qualname || (m.module ? `${m.module}.${m.class_name}` : m.class_name)) ? 'bg-gray-200 dark:bg-gray-700' : ''} hover:bg-indigo-50 active:scale-[.99] active:bg-indigo-100 dark:hover:bg-indigo-950/40 dark:active:bg-indigo-900/60`}
													onclick={() => selectReq(r, m)}
												>
													<div class="flex items-start gap-3">
														<div>
															<div class="font-medium">{displayName(m)}</div>
															<div class="truncate text-[10px] text-gray-500 dark:text-gray-400">
																{displaySub(m)}
															</div>
														</div>
													</div>
												</button>
											</li>
										{/each}
									</ul>
								{:else}
									<div class="px-2 py-3 text-sm text-gray-600 dark:text-gray-300">
										No supported instruments found.
									</div>
								{/if}
							</ScrollArea.Viewport>
							<ScrollArea.Scrollbar
								orientation="vertical"
								class="bg-muted hover:bg-dark-10 data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0 data-[state=visible]:fade-in-0 flex w-2.5 touch-none select-none rounded-full border-l border-l-transparent p-px transition-all duration-200 hover:w-3"
							>
								<ScrollArea.Thumb class="bg-muted-foreground flex-1 rounded-full" />
							</ScrollArea.Scrollbar>
							<ScrollArea.Corner />
						</ScrollArea.Root>
					</section>
				{/each}
			</div>
		{/if}
	{/if}
</section>

{#if measurementName}
	<div class="mt-6 flex justify-end">
		<button
			class="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50"
			onclick={onNext}
			disabled={!allSelected}
		>
			Next
		</button>
	</div>
{/if}
