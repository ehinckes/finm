module.exports = {
    content: [
        // Paths to Django template files that will contain Tailwind CSS classes.
        '../templates/**/*.html',
        '../../templates/**/*.html',
        '../../**/templates/**/*.html',
    ],
    theme: {
        extend: {
            colors: {
                'custom-green-pale': '#D6EFD8',
                'custom-green-light': '#80AF81',
                'custom-green-full': '#508D4E',
                'custom-green-dark': '#1A5319',
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
