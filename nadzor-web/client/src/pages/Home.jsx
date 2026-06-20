import React, { useState, useEffect } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';

function Home() {

    const [state, setState] = useState(null);
    const [currentUser, setCurrentUser] = useState(null);

    const [count, setCount] = useLocalStorage( 'savedClickCount', 0 );

    const callBackendAPI = async () => {
        const responce = await fetch('/api');
        const body = await responce.json();

        if (responce.status !== 200) {
           throw Error();
        }

        return body;
    };

    useEffect( () => {
        callBackendAPI()
        .then(res => setState(res.express))
        .catch(err => console.log(err))
    }, [])

    return (        
        <div>
            <div>{state}</div>
            <div>amogys</div>
            <br/>

            <p> 
                Тут пока ничего особенно нет. <br />
                Выбери любую страницу сверху  <br />
                Или кликните ещё раз: { count } <button className="icon" onClick={ () => setCount(0) }> 󰑓 </button> <br />
            </p>

            <button onClick={() => setCount( count + 1 )}>
                Кликни меня!!
            </button>
        </div>
    );
}

export default Home;
