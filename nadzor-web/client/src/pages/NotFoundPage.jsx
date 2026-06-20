import React from 'react';
import { Link } from 'react-router-dom';

function NotFoundPage() {
    return (
        <div className="not-found-container">
            <h1>404</h1>
            <p>Страничка не найдена</p>
            <h1>:(</h1>
            <Link to="/" className="home-link">Вернуться додому</Link>
        </div>
    );
}

export default NotFoundPage;
