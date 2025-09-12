<script lang="ts">
	import { Tooltip } from 'bits-ui';
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		children: Snippet;
		onclick: () => void;
	}

	let { label, children, onclick }: Props = $props();
</script>

<Tooltip.Provider>
	<Tooltip.Root delayDuration={200}>
		<Tooltip.Trigger class="inline-flex items-center justify-center">
			<button type="button" class="icon-holder" {onclick} aria-label={label} title={label}>
				{@render children()}
			</button>
		</Tooltip.Trigger>
		<Tooltip.Content side={'right'} sideOffset={8}>
			<div
				class="rounded-input border-dark-10 bg-background shadow-popover outline-hidden z-0 flex items-center justify-center border p-3 text-sm font-medium"
			>
				{label}
			</div>
		</Tooltip.Content>
	</Tooltip.Root>
</Tooltip.Provider>

<style>
	.icon-holder {
		display: flex;
		justify-content: center;
		align-items: center;
		width: 1.8rem;
		height: 1.8rem;
		border-radius: 0.375rem;
		color: rgb(127, 127, 127);
		cursor: pointer;
		margin-bottom: 0.3rem;
		background-color: transparent;
		border: none;
		padding: 0;
	}

	.icon-holder:hover {
		background-color: #ededed;
		border-radius: 0.3rem;
	}

	.icon-holder:active {
		color: #000000;
	}

	@media (max-width: 500px) {
		.icon-holder {
			margin-bottom: 0;
			margin-right: 0.25rem;
		}
	}
</style>
