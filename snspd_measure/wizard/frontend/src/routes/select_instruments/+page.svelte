<script lang="ts">
	let { data } = $props();
	const measurementName: string | null = data.measurementName;
	const instruments: string[] = data.instruments ?? [];
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

	<div
		class="rounded-xl border border-gray-200 bg-white/70 p-4 dark:border-white/10 dark:bg-gray-800/70"
	>
		{#if !measurementName}
			<div class="text-sm text-gray-600 dark:text-gray-300">Select a measurement first.</div>
		{:else if instruments.length === 0}
			<div class="text-sm text-gray-600 dark:text-gray-300">No instrument roles detected.</div>
		{:else}
			<ul class="list-disc pl-6">
				{#each instruments as role}
					<li>{role}</li>
				{/each}
			</ul>
		{/if}
	</div>
</section>
