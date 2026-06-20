import { useState, useEffect } from 'react';

export function useLocalStorage(key, initialValue) {

    const [value, setValue] = useState( () => {
        const savedValue = localStorage.getItem( key );
        return savedValue ? parseInt( savedValue, 10 ) : initialValue;
    });

    useEffect( () => {
    
        localStorage.setItem( key, JSON.stringify(value) );
    
    }, [key, value]);

    return [value, setValue];

}
