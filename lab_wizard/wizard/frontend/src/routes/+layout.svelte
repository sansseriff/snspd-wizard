<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import TooltipIcon from '$lib/components/TooltipIcon.svelte';
	import House from 'phosphor-svelte/lib/House';
	import Plus from 'phosphor-svelte/lib/Plus';
	import PencilSimple from 'phosphor-svelte/lib/PencilSimple';
	import ThermometerSimple from 'phosphor-svelte/lib/ThermometerSimple';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div
	class="flex min-h-screen flex-col bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100"
>
	<header
		class="sticky top-0 z-10 border-b border-gray-200/70 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:border-white/10 dark:bg-gray-900/70"
	>
		<div class="mx-auto flex h-12 max-w-6xl items-center justify-between px-3 sm:px-4 lg:px-6">
			<a
				href="/"
				class="inline-flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400"
			>
				<House size={20} weight="duotone" />
				<span class="hidden sm:inline">Home</span>
			</a>

			<nav class="hidden items-center gap-2 sm:flex">
				<!-- <TooltipIcon label="New" href="/create_measurement">
					<Plus size={18} weight="bold" />
				</TooltipIcon>
				<TooltipIcon label="Edit" href="/creat_custom_resource">
					<PencilSimple size={18} weight="bold" />
				</TooltipIcon>
				<TooltipIcon label="Temp">
					<ThermometerSimple size={18} weight="bold" />
				</TooltipIcon> -->
			</nav>
		</div>
	</header>

	<main class="flex-1">
		<div class="mx-auto max-w-6xl px-3 py-6 sm:px-4 lg:px-6">
			{@render children?.()}
		</div>
	</main>
</div>
