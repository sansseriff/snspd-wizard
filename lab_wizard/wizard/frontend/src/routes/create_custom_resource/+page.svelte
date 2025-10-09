<script lang="ts">
	import PencilSimple from 'phosphor-svelte/lib/PencilSimple';
	let loading = false;
	let { data } = $props();
	const types: Array<{ id: string; label: string }> = data?.meta?.types ?? [];
</script>

<section class="space-y-4">
	<h1 class="text-2xl font-semibold">Create Custom Resource</h1>
	<p class="text-sm text-gray-600 dark:text-gray-300">
		Define a reusable instrument or component. This page will be populated with schema-driven forms
		later.
	</p>

	<div
		class="rounded-xl border border-gray-200 bg-white/70 p-4 dark:border-white/10 dark:bg-gray-800/70"
	>
		<div class="grid gap-3 sm:grid-cols-2">
			<label class="block">
				<span class="text-xs text-gray-600 dark:text-gray-300">Name</span>
				<input
					class="mt-1 w-full rounded-md border border-gray-300 bg-white/90 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900"
					placeholder="My resource"
				/>
			</label>
			<label class="block">
				<span class="text-xs text-gray-600 dark:text-gray-300">Type</span>
				<select
					class="mt-1 w-full rounded-md border border-gray-300 bg-white/90 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900"
				>
					{#each types as t}
						<option value={t.id}>{t.label}</option>
					{/each}
				</select>
			</label>
		</div>

		<div class="mt-4">
			<button
				class="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 disabled:opacity-50"
				disabled={loading}
			>
				<PencilSimple size={18} />
				Save
			</button>
		</div>
	</div>
</section>
