<script lang="ts">
	import { ScrollArea } from 'bits-ui';
	import { goto } from '$app/navigation';
	type MeasurementInfo = { name: string; description: string; measurement_dir: string };
	let loading = false;
	let { data } = $props();
	const measurements: MeasurementInfo[] = (data?.measurements ?? []) as MeasurementInfo[];
	let selectedName = $state<string | null>(null);
	// let selected: MeasurementInfo | null = $state(null);

	function onNext() {
		if (!selectedName) return;
		goto(`/select_instruments?name=${encodeURIComponent(selectedName)}`);
	}
</script>

<section class="space-y-4">
	<h1 class="text-2xl font-semibold">Choose a measurement</h1>
	<p class="text-sm text-gray-600 dark:text-gray-300">
		Pick a measurement type, then continue to select instruments.
	</p>

	<ScrollArea.Root
		class="relative overflow-hidden rounded-xl border border-gray-200 bg-white/70 p-3 shadow-sm dark:border-white/10 dark:bg-gray-800/70"
	>
		<ScrollArea.Viewport class="h-full max-h-[360px] w-full">
			<ul class="divide-y divide-gray-200 dark:divide-white/10">
				{#each measurements as m}
					<li>
						<button
							class={`w-full rounded-md px-3 py-3 text-left transition ${selectedName === m.name ? 'bg-gray-200 dark:bg-gray-700' : ''} hover:bg-indigo-50 active:scale-[.99] active:bg-indigo-100 dark:hover:bg-indigo-950/40 dark:active:bg-indigo-900/60`}
							onclick={() => (selectedName = m.name)}
						>
							<div class="flex items-start gap-3">
								<div>
									<div class="font-medium">{m.name}</div>
									<div class="text-xs text-gray-600 dark:text-gray-300">{m.description}</div>
									<div class="truncate text-[10px] text-gray-500 dark:text-gray-400">
										{m.measurement_dir}
									</div>
								</div>
							</div>
						</button>
					</li>
				{/each}
			</ul>
		</ScrollArea.Viewport>
		<ScrollArea.Scrollbar
			orientation="vertical"
			class="bg-muted hover:bg-dark-10 data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0 data-[state=visible]:fade-in-0 flex w-2.5 touch-none select-none rounded-full border-l border-l-transparent p-px transition-all duration-200 hover:w-3"
		>
			<ScrollArea.Thumb class="bg-muted-foreground flex-1 rounded-full" />
		</ScrollArea.Scrollbar>
		<ScrollArea.Corner />
	</ScrollArea.Root>

	<div class="flex justify-end">
		<button
			class="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 disabled:opacity-50"
			onclick={onNext}
			disabled={!selectedName || loading}
		>
			Next
		</button>
	</div>
</section>
