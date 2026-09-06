// Theo dõi DOM thay đổi và gắn class CSS chớp nháy siêu tốc
document.addEventListener('DOMContentLoaded', function() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'characterData' || mutation.type === 'childList') {
                let target = mutation.target;
                while (target && target.tagName !== 'g') target = target.parentNode;

                if (target && target.classList.contains('trace')) {
                    const surface = target.querySelector('path.surface');
                    if (surface) {
                        surface.classList.remove('flash-active');
                        void surface.offsetWidth; // Trigger reflow
                        surface.classList.add('flash-active');
                        setTimeout(() => surface.classList.remove('flash-active'), 300);
                    }
                }
            }
        });
    });

    const startObserving = () => {
        const graphContainer = document.getElementById('heatmap-graph');
        if (graphContainer) {
            observer.observe(graphContainer, { childList: true, subtree: true, characterData: true });
        } else {
            setTimeout(startObserving, 500);
        }
    };
    startObserving();
});